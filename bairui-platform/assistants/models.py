import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Assistant(TimestampedModel):
    class Scene(models.TextChoices):
        STUDY = "study", "学习"
        LIFE = "life", "生活"
        RESEARCH = "research", "研究"
        WORK = "work", "工作"
        CREATION = "creation", "创作"
        CUSTOM = "custom", "自定义"

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PENDING = "pending", "等待审批"
        PROVISIONING = "provisioning", "配置中"
        ACTIVE = "active", "运行中"
        SUSPENDED = "suspended", "已暂停"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assistants")
    name = models.CharField(max_length=64)
    scene = models.CharField(max_length=24, choices=Scene.choices, default=Scene.RESEARCH)
    goal = models.TextField(blank=True)
    tone = models.CharField(max_length=32, default="研究型")
    model_name = models.CharField(max_length=64, default="gpt-5.5")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    workspace_path = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.name} ({self.owner})"


class Plan(TimestampedModel):
    code = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    monthly_price_cents = models.PositiveIntegerField(default=0)
    assistant_limit = models.PositiveSmallIntegerField(default=1)
    task_limit_monthly = models.PositiveIntegerField(default=100)
    storage_limit_mb = models.PositiveIntegerField(default=512)
    memory_enabled = models.BooleanField(default=False)
    advanced_tools_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Subscription(TimestampedModel):
    class Status(models.TextChoices):
        TRIAL = "trial", "试用"
        ACTIVE = "active", "有效"
        PAST_DUE = "past_due", "待续费"
        CANCELED = "canceled", "已取消"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.TRIAL)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.plan}"


class UsageMeter(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_meters")
    period = models.CharField(max_length=7, help_text="YYYY-MM")
    task_count = models.PositiveIntegerField(default=0)
    tool_call_count = models.PositiveIntegerField(default=0)
    storage_used_mb = models.PositiveIntegerField(default=0)
    premium_model_call_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "period"], name="unique_usage_period_per_user"),
        ]

    def __str__(self):
        return f"{self.user} usage {self.period}"


class AssistantToolProfile(TimestampedModel):
    assistant = models.OneToOneField(Assistant, on_delete=models.CASCADE, related_name="tools")
    browser_enabled = models.BooleanField(default=True)
    files_enabled = models.BooleanField(default=True)
    memory_enabled = models.BooleanField(default=False)
    cron_enabled = models.BooleanField(default=False)
    subagents_enabled = models.BooleanField(default=True)
    code_enabled = models.BooleanField(default=False)
    approval_required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.assistant.name} tools"


class ProvisionRequest(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "待审批"
        APPROVED = "approved", "已批准"
        REJECTED = "rejected", "已拒绝"
        DONE = "done", "已完成"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="provision_requests")
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name="provision_requests")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    admin_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.assistant.name} - {self.get_status_display()}"


class RuntimeBinding(TimestampedModel):
    class RuntimeType(models.TextChoices):
        HERMES = "hermes", "Hermes"
        LOCAL = "local", "Local Worker"
        EXTERNAL = "external", "External Runtime"

    assistant = models.OneToOneField(Assistant, on_delete=models.CASCADE, related_name="runtime")
    runtime_type = models.CharField(max_length=24, choices=RuntimeType.choices, default=RuntimeType.HERMES)
    endpoint = models.CharField(max_length=255, blank=True)
    runtime_agent_id = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.assistant.name} runtime"


class DeviceBinding(TimestampedModel):
    class DeviceType(models.TextChoices):
        DESKTOP = "desktop", "Desktop"
        CLI = "cli", "CLI"
        SERVER = "server", "Server"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        REVOKED = "revoked", "Revoked"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_bindings")
    public_device_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=120)
    device_type = models.CharField(max_length=24, choices=DeviceType.choices, default=DeviceType.DESKTOP)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    pairing_code_hash = models.CharField(max_length=128, blank=True)
    pairing_code_expires_at = models.DateTimeField(null=True, blank=True)
    pairing_attempts = models.PositiveSmallIntegerField(default=0)
    agent_token_hash = models.CharField(max_length=128, blank=True)
    paired_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["public_device_id"]),
        ]
        ordering = ["-updated_at"]

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE and self.revoked_at is None

    @property
    def can_pair(self):
        return (
            self.status == self.Status.PENDING
            and self.pairing_code_hash
            and self.pairing_code_expires_at is not None
            and self.pairing_code_expires_at > timezone.now()
            and self.pairing_attempts < 5
        )

    def __str__(self):
        return f"{self.name} ({self.user})"


class LocalAgent(TimestampedModel):
    class Transport(models.TextChoices):
        WEBSOCKET = "websocket", "WebSocket"
        GRPC = "grpc", "gRPC"
        POLLING = "polling", "Polling"

    class Status(models.TextChoices):
        OFFLINE = "offline", "Offline"
        ONLINE = "online", "Online"
        ERROR = "error", "Error"

    device = models.OneToOneField(DeviceBinding, on_delete=models.CASCADE, related_name="local_agent")
    version = models.CharField(max_length=32, blank=True)
    transport = models.CharField(max_length=24, choices=Transport.choices, default=Transport.WEBSOCKET)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OFFLINE)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    capabilities = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["transport"]),
        ]
        ordering = ["-updated_at"]

    @property
    def is_online(self):
        return self.status == self.Status.ONLINE

    def __str__(self):
        return f"{self.device.name} local agent"


class WorkspaceBinding(TimestampedModel):
    class Mode(models.TextChoices):
        CLOUD_FILES = "cloud_files", "Cloud Files"
        GIT = "git", "Git Workspace"
        LOCAL = "local", "Local Agent"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        REVOKED = "revoked", "Revoked"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspace_bindings")
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name="workspace_bindings", null=True, blank=True)
    device = models.ForeignKey(DeviceBinding, on_delete=models.SET_NULL, related_name="workspace_bindings", null=True, blank=True)
    public_workspace_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    mode = models.CharField(max_length=24, choices=Mode.choices, default=Mode.CLOUD_FILES)
    display_name = models.CharField(max_length=120)
    local_path_hint = models.CharField(max_length=500, blank=True)
    git_remote_url = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ACTIVE)
    policy = models.JSONField(default=dict, blank=True)
    last_indexed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "mode"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["public_workspace_id"]),
        ]
        ordering = ["-updated_at"]

    def clean(self):
        errors = {}
        if self.assistant_id and self.assistant.owner_id != self.owner_id:
            errors["assistant"] = "Assistant must belong to the workspace owner."
        if self.device_id and self.device.user_id != self.owner_id:
            errors["device"] = "Device must belong to the workspace owner."
        if self.mode == self.Mode.LOCAL and self.git_remote_url:
            errors["git_remote_url"] = "Local workspaces should not store a Git remote URL."
        if self.mode == self.Mode.GIT and self.local_path_hint:
            errors["local_path_hint"] = "Git workspaces should not store a local path hint."
        if errors:
            raise ValidationError(errors)

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE and self.revoked_at is None

    def __str__(self):
        return f"{self.display_name} ({self.get_mode_display()})"


class AssistantStorage(TimestampedModel):
    assistant = models.OneToOneField(Assistant, on_delete=models.CASCADE, related_name="storage")
    quota_mb = models.PositiveIntegerField(default=512)
    used_mb = models.PositiveIntegerField(default=0)
    root_path = models.CharField(max_length=255)
    workspace_path = models.CharField(max_length=255)
    files_path = models.CharField(max_length=255)
    memory_path = models.CharField(max_length=255)
    logs_path = models.CharField(max_length=255)

    @property
    def available_mb(self):
        return max(self.quota_mb - self.used_mb, 0)

    def __str__(self):
        return f"{self.assistant.name} storage"


class AssistantFile(TimestampedModel):
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name="files")
    storage = models.ForeignKey(AssistantStorage, on_delete=models.CASCADE, related_name="files")
    original_name = models.CharField(max_length=255)
    stored_name = models.CharField(max_length=255)
    path = models.CharField(max_length=500)
    size_bytes = models.PositiveBigIntegerField(default=0)
    size_mb = models.PositiveIntegerField(default=0)
    content_type = models.CharField(max_length=128, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_assistant_files")

    def __str__(self):
        return self.original_name


class AssistantTask(TimestampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "排队中"
        RUNNING = "running", "运行中"
        SUCCEEDED = "succeeded", "已完成"
        FAILED = "failed", "失败"

    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name="tasks")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assistant_tasks")
    title = models.CharField(max_length=120, default="Untitled task")
    task_type = models.CharField(max_length=64)
    prompt = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.QUEUED)
    progress = models.PositiveSmallIntegerField(default=0)
    result_summary = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.assistant.name} {self.title}"


class AssistantLog(TimestampedModel):
    class Level(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.INFO)
    source = models.CharField(max_length=64, default="platform")
    message = models.TextField()

    def __str__(self):
        return f"{self.level}: {self.message[:48]}"


class MemoryItem(TimestampedModel):
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name="memory_items")
    kind = models.CharField(max_length=64, default="note")
    content = models.TextField()

    def __str__(self):
        return f"{self.assistant.name} memory {self.kind}"


class InvitationCode(TimestampedModel):
    code = models.CharField(max_length=64, unique=True)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="invitation_codes", null=True, blank=True)
    max_redemptions = models.PositiveIntegerField(default=1)
    redemption_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code


class AuditEvent(TimestampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="audit_events", null=True, blank=True)
    action = models.CharField(max_length=96)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.action


class EmailLoginCode(TimestampedModel):
    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    @property
    def is_usable(self):
        return self.consumed_at is None and self.expires_at > timezone.now() and self.attempts < 5

    def __str__(self):
        return f"{self.email} login code"
