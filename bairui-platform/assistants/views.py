import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import (
    Assistant,
    AssistantFile,
    AssistantLog,
    AssistantStorage,
    AssistantTask,
    AuditEvent,
    DeviceBinding,
    EmailLoginCode,
    LocalAgent,
    MemoryItem,
    Plan,
    ProvisionRequest,
    RuntimeBinding,
    Subscription,
    UsageMeter,
)
from .serializers import (
    AssistantSerializer,
    AssistantTaskSerializer,
    CompleteDevicePairingSerializer,
    CreateDevicePairingCodeSerializer,
    DeviceBindingSerializer,
    AssistantFileSerializer,
    AssistantLogSerializer,
    LoginSerializer,
    MemoryItemSerializer,
    PlanSerializer,
    ProvisionRequestSerializer,
    RequestEmailCodeSerializer,
    RegisterSerializer,
    UserSerializer,
    VerifyEmailCodeSerializer,
)
from .storage import allocate_file, append_memory_item, ensure_storage_directories

User = get_user_model()


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response(
        {
            "status": "ok",
            "service": "bairui-platform",
            "runtime": "django",
            "api": "portal-api",
        }
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    login(request, user)
    return Response(UserSerializer(user).data, status=201)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def request_email_code(request):
    serializer = RequestEmailCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    recent_count = EmailLoginCode.objects.filter(email=email, created_at__gte=timezone.now() - timedelta(minutes=1)).count()
    if recent_count >= 1:
        raise ValidationError({"email": "验证码发送过于频繁，请稍后再试。"})

    code = f"{secrets.randbelow(1_000_000):06d}"
    EmailLoginCode.objects.create(
        email=email,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(minutes=settings.EMAIL_LOGIN_CODE_TTL_MINUTES),
        ip_address=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
    )
    send_mail(
        "百瑞云代理登录验证码",
        f"你的百瑞云代理登录验证码是：{code}\n\n验证码 {settings.EMAIL_LOGIN_CODE_TTL_MINUTES} 分钟内有效。如非本人操作，请忽略本邮件。",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    return Response({"status": "sent", "expires_in_minutes": settings.EMAIL_LOGIN_CODE_TTL_MINUTES})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def verify_email_code(request):
    serializer = VerifyEmailCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    code = serializer.validated_data["code"]
    invalid_code = False
    with transaction.atomic():
        login_code = EmailLoginCode.objects.select_for_update().filter(email=email, consumed_at__isnull=True).order_by("-created_at").first()
        if login_code is None or not login_code.is_usable:
            raise ValidationError({"code": "验证码已过期或不可用。"})
        login_code.attempts += 1
        invalid_code = not check_password(code, login_code.code_hash)
        if invalid_code:
            login_code.save(update_fields=["attempts", "updated_at"])
        else:
            login_code.consumed_at = timezone.now()
            login_code.save(update_fields=["attempts", "consumed_at", "updated_at"])

    if invalid_code:
        raise ValidationError({"code": "验证码错误。"})
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        username = _unique_username_from_email(email)
        user = User.objects.create_user(username=username, email=email, password=None)
        starter = Plan.objects.filter(code="starter", is_active=True).first()
        if starter:
            Subscription.objects.create(user=user, plan=starter)
    login(request, user)
    AuditEvent.objects.create(actor=user, action="auth.email_code_login", target_type="user", target_id=str(user.id), ip_address=_client_ip(request))
    return Response(UserSerializer(user).data)


class AssistantViewSet(viewsets.ModelViewSet):
    serializer_class = AssistantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Assistant.objects.filter(owner=self.request.user).select_related("tools").order_by("-updated_at")

    def perform_create(self, serializer):
        subscription = getattr(self.request.user, "subscription", None)
        if subscription:
            current_count = Assistant.objects.filter(owner=self.request.user).count()
            if current_count >= subscription.plan.assistant_limit:
                raise ValidationError({"plan": "当前套餐可创建的助理数量已达上限。"})
        serializer.save()

    @action(detail=True, methods=["GET", "POST"])
    def tasks(self, request, pk=None):
        assistant = self.get_object()
        if request.method == "GET":
            tasks = AssistantTask.objects.filter(assistant=assistant).order_by("-created_at")
            return Response(AssistantTaskSerializer(tasks, many=True).data)

        if assistant.status != Assistant.Status.ACTIVE:
            raise ValidationError({"assistant": "助理尚未激活，不能创建任务。"})
        subscription = getattr(request.user, "subscription", None)
        plan = subscription.plan if subscription else None
        period = timezone.now().strftime("%Y-%m")
        meter, _ = UsageMeter.objects.get_or_create(user=request.user, period=period)
        if plan and meter.task_count >= plan.task_limit_monthly:
            raise ValidationError({"plan": "当前套餐本月任务额度已用完。"})

        serializer = AssistantTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(
            assistant=assistant,
            created_by=request.user,
            status=AssistantTask.Status.QUEUED,
            progress=0,
            result_summary="任务已进入队列，等待运行时接入 Hermes/Celery 执行。",
        )
        meter.task_count += 1
        meter.save(update_fields=["task_count", "updated_at"])
        AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.INFO, source="tasks", message=f"新建任务：{task.title}")
        return Response(AssistantTaskSerializer(task).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["GET"])
    def files(self, request, pk=None):
        assistant = self.get_object()
        files = AssistantFile.objects.filter(assistant=assistant).order_by("-created_at")
        return Response(AssistantFileSerializer(files, many=True).data)

    @action(detail=True, methods=["POST"])
    def upload_file(self, request, pk=None):
        assistant = self.get_object()
        if assistant.status != Assistant.Status.ACTIVE:
            raise ValidationError({"assistant": "助理尚未激活，不能上传文件。"})
        storage = getattr(assistant, "storage", None)
        if storage is None:
            raise ValidationError({"storage": "助理尚未分配存储空间。"})
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            raise ValidationError({"file": "请选择要上传的文件。"})
        path, size_bytes, size_mb = allocate_file(storage, uploaded_file)
        record = AssistantFile.objects.create(
            assistant=assistant,
            storage=storage,
            original_name=uploaded_file.name,
            stored_name=path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
            path=path,
            size_bytes=size_bytes,
            size_mb=size_mb,
            content_type=getattr(uploaded_file, "content_type", "") or "",
            uploaded_by=request.user,
        )
        AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.INFO, source="files", message=f"上传文件：{record.original_name}")
        return Response(AssistantFileSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["GET", "POST"])
    def memory(self, request, pk=None):
        assistant = self.get_object()
        if request.method == "GET":
            items = MemoryItem.objects.filter(assistant=assistant).order_by("-created_at")
            return Response(MemoryItemSerializer(items, many=True).data)

        if assistant.status != Assistant.Status.ACTIVE:
            raise ValidationError({"assistant": "助理尚未激活，不能写入长期记忆。"})
        if not getattr(getattr(assistant, "tools", None), "memory_enabled", False):
            raise ValidationError({"memory": "该助理未开启长期记忆能力。"})
        subscription = getattr(request.user, "subscription", None)
        if subscription and not subscription.plan.memory_enabled:
            raise ValidationError({"plan": "当前套餐未开通长期记忆能力。"})
        storage = getattr(assistant, "storage", None)
        if storage is None:
            raise ValidationError({"storage": "助理尚未分配记忆空间。"})

        serializer = MemoryItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(assistant=assistant)
        append_memory_item(storage, item)
        AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.INFO, source="memory", message=f"新增长期记忆：{item.kind}")
        return Response(MemoryItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["GET"])
    def logs(self, request, pk=None):
        assistant = self.get_object()
        logs = AssistantLog.objects.filter(assistant=assistant).order_by("-created_at")[:200]
        return Response(AssistantLogSerializer(logs, many=True).data)


class DeviceBindingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeviceBindingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeviceBinding.objects.filter(user=self.request.user).order_by("-updated_at")

    @action(detail=False, methods=["POST"], url_path="pairing-code")
    def create_pairing_code(self, request):
        serializer = CreateDevicePairingCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = _generate_pairing_code()
        expires_at = timezone.now() + timedelta(minutes=10)
        device = DeviceBinding.objects.create(
            user=request.user,
            name=serializer.validated_data["name"],
            device_type=serializer.validated_data["device_type"],
            pairing_code_hash=make_password(code),
            pairing_code_expires_at=expires_at,
            metadata=serializer.validated_data.get("metadata", {}),
        )
        AuditEvent.objects.create(
            actor=request.user,
            action="device.pairing_code_created",
            target_type="device",
            target_id=str(device.public_device_id),
            ip_address=_client_ip(request),
        )
        data = DeviceBindingSerializer(device).data
        data["pairing_code"] = code
        data["expires_in_seconds"] = 600
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"])
    def revoke(self, request, pk=None):
        device = self.get_object()
        device.status = DeviceBinding.Status.REVOKED
        device.revoked_at = timezone.now()
        device.agent_token_hash = ""
        device.pairing_code_hash = ""
        device.save(update_fields=["status", "revoked_at", "agent_token_hash", "pairing_code_hash", "updated_at"])
        LocalAgent.objects.filter(device=device).update(status=LocalAgent.Status.OFFLINE, updated_at=timezone.now())
        AuditEvent.objects.create(
            actor=request.user,
            action="device.revoked",
            target_type="device",
            target_id=str(device.public_device_id),
            ip_address=_client_ip(request),
        )
        return Response(DeviceBindingSerializer(device).data)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def complete_device_pairing(request):
    serializer = CompleteDevicePairingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    pairing_code = serializer.validated_data["pairing_code"]
    public_device_id = serializer.validated_data["public_device_id"]
    invalid_code = False
    with transaction.atomic():
        device = DeviceBinding.objects.select_for_update().filter(public_device_id=public_device_id).first()
        if device is None or not device.can_pair:
            raise ValidationError({"pairing_code": "Pairing code expired or device cannot be paired."})
        device.pairing_attempts += 1
        invalid_code = not check_password(pairing_code, device.pairing_code_hash)
        if invalid_code:
            device.save(update_fields=["pairing_attempts", "updated_at"])
        else:
            agent_token = secrets.token_urlsafe(32)
            now = timezone.now()
            device.status = DeviceBinding.Status.ACTIVE
            device.paired_at = now
            device.last_seen_at = now
            device.agent_token_hash = make_password(agent_token)
            device.pairing_code_hash = ""
            device.save(
                update_fields=[
                    "status",
                    "paired_at",
                    "last_seen_at",
                    "agent_token_hash",
                    "pairing_code_hash",
                    "pairing_attempts",
                    "updated_at",
                ]
            )
            agent, _ = LocalAgent.objects.update_or_create(
                device=device,
                defaults={
                    "version": serializer.validated_data.get("agent_version", ""),
                    "transport": serializer.validated_data["transport"],
                    "status": LocalAgent.Status.OFFLINE,
                    "last_heartbeat_at": now,
                    "capabilities": serializer.validated_data.get("capabilities", {}),
                    "metadata": serializer.validated_data.get("metadata", {}),
                },
            )

    if invalid_code:
        raise ValidationError({"pairing_code": "Invalid pairing code."})

    AuditEvent.objects.create(
        actor=device.user,
        action="device.paired",
        target_type="device",
        target_id=str(device.public_device_id),
        ip_address=_client_ip(request),
        metadata={"transport": agent.transport, "agent_version": agent.version},
    )
    return Response(
        {
            "device": DeviceBindingSerializer(device).data,
            "agent_token": agent_token,
            "token_type": "Bearer",
        }
    )


class ProvisionRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ProvisionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return ProvisionRequest.objects.select_related("assistant", "user").order_by("-created_at")
        return ProvisionRequest.objects.filter(user=self.request.user).select_related("assistant").order_by("-created_at")

    @transaction.atomic
    def perform_create(self, serializer):
        assistant = serializer.validated_data["assistant"]
        if assistant.owner_id != self.request.user.id:
            raise PermissionDenied("Cannot provision another user's assistant.")
        if ProvisionRequest.objects.filter(assistant=assistant, status=ProvisionRequest.Status.PENDING).exists():
            raise ValidationError({"assistant": "该助理已有待审批开通申请。"})
        assistant.status = Assistant.Status.PENDING
        assistant.save(update_fields=["status", "updated_at"])
        request_obj = serializer.save(user=self.request.user)
        AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.INFO, source="platform", message="开通申请已提交。")
        AuditEvent.objects.create(
            actor=self.request.user,
            action="provision.requested",
            target_type="assistant",
            target_id=str(assistant.id),
            metadata={"provision_request_id": request_obj.id},
        )

    @action(detail=True, methods=["POST"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        provision_request = self.get_object()
        assistant = provision_request.assistant
        storage = _storage_paths_for_assistant(assistant)
        provision_request.status = ProvisionRequest.Status.APPROVED
        provision_request.admin_note = request.data.get("admin_note", provision_request.admin_note)
        provision_request.save(update_fields=["status", "admin_note", "updated_at"])
        assistant.status = Assistant.Status.ACTIVE
        assistant.workspace_path = assistant.workspace_path or storage["workspace_path"]
        assistant.save(update_fields=["status", "workspace_path", "updated_at"])
        RuntimeBinding.objects.get_or_create(assistant=assistant, defaults={"runtime_type": RuntimeBinding.RuntimeType.HERMES, "is_active": True})
        storage_record, _ = AssistantStorage.objects.update_or_create(
            assistant=assistant,
            defaults={
                "quota_mb": _storage_quota_for_user(assistant.owner),
                **storage,
            },
        )
        ensure_storage_directories(storage_record)
        AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.INFO, source="admin", message="开通申请已批准，助理已激活。")
        AuditEvent.objects.create(
            actor=request.user,
            action="provision.approved",
            target_type="assistant",
            target_id=str(assistant.id),
            metadata={"provision_request_id": provision_request.id},
        )
        return Response(self.get_serializer(provision_request).data)

    @action(detail=True, methods=["POST"], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        provision_request = self.get_object()
        assistant = provision_request.assistant
        provision_request.status = ProvisionRequest.Status.REJECTED
        provision_request.admin_note = request.data.get("admin_note", provision_request.admin_note)
        provision_request.save(update_fields=["status", "admin_note", "updated_at"])
        assistant.status = Assistant.Status.DRAFT
        assistant.save(update_fields=["status", "updated_at"])
        AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.WARNING, source="admin", message="开通申请已拒绝。")
        AuditEvent.objects.create(
            actor=request.user,
            action="provision.rejected",
            target_type="assistant",
            target_id=str(assistant.id),
            metadata={"provision_request_id": provision_request.id},
        )
        return Response(self.get_serializer(provision_request).data)


class PublicPlanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Plan.objects.filter(is_active=True).order_by("monthly_price_cents", "id")


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _unique_username_from_email(email):
    base = email.split("@", 1)[0].replace(".", "_").replace("-", "_")[:120] or "user"
    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        suffix += 1
        candidate = f"{base}_{suffix}"[:150]
    return candidate


def _generate_pairing_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(8))


def _storage_quota_for_user(user):
    subscription = getattr(user, "subscription", None)
    if subscription:
        return subscription.plan.storage_limit_mb
    starter = Plan.objects.filter(code="starter", is_active=True).first()
    return starter.storage_limit_mb if starter else 512


def _storage_paths_for_assistant(assistant):
    root = settings.ASSISTANT_STORAGE_ROOT.rstrip("/")
    assistant_root = f"{root}/user-{assistant.owner_id}/assistant-{assistant.id}"
    return {
        "root_path": assistant_root,
        "workspace_path": f"{assistant_root}/workspace",
        "files_path": f"{assistant_root}/files",
        "memory_path": f"{assistant_root}/memory",
        "logs_path": f"{assistant_root}/logs",
    }
