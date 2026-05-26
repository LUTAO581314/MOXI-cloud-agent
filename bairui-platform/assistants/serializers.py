from django.contrib.auth import authenticate, get_user_model
from django.core.validators import validate_email
from rest_framework import serializers

from .models import (
    Assistant,
    AssistantFile,
    AssistantLog,
    AssistantStorage,
    AssistantTask,
    AssistantToolProfile,
    DeviceBinding,
    EmailLoginCode,
    LocalAgent,
    MemoryItem,
    Plan,
    ProvisionRequest,
    Subscription,
    UsageMeter,
    WorkspaceBinding,
)

User = get_user_model()


class AssistantToolProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantToolProfile
        fields = [
            "browser_enabled",
            "files_enabled",
            "memory_enabled",
            "cron_enabled",
            "subagents_enabled",
            "code_enabled",
            "approval_required",
        ]


class AssistantStorageSerializer(serializers.ModelSerializer):
    available_mb = serializers.IntegerField(read_only=True)

    class Meta:
        model = AssistantStorage
        fields = [
            "quota_mb",
            "used_mb",
            "available_mb",
            "root_path",
            "workspace_path",
            "files_path",
            "memory_path",
            "logs_path",
        ]
        read_only_fields = fields


class AssistantFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantFile
        fields = [
            "id",
            "assistant",
            "original_name",
            "stored_name",
            "size_bytes",
            "size_mb",
            "content_type",
            "created_at",
        ]
        read_only_fields = fields


class MemoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryItem
        fields = ["id", "assistant", "kind", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "assistant", "created_at", "updated_at"]

    def validate_kind(self, value):
        value = (value or "note").strip().lower()
        if not value:
            return "note"
        if len(value) > 64:
            raise serializers.ValidationError("记忆类型不能超过 64 个字符。")
        return value

    def validate_content(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("记忆内容不能为空。")
        if len(value) > 4000:
            raise serializers.ValidationError("单条记忆不能超过 4000 个字符。")
        return value


class AssistantTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantTask
        fields = [
            "id",
            "assistant",
            "title",
            "task_type",
            "prompt",
            "status",
            "progress",
            "result_summary",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        read_only_fields = ["id", "assistant", "status", "progress", "result_summary", "created_at", "updated_at", "completed_at"]

    def validate_title(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("任务标题不能为空。")
        if len(value) > 120:
            raise serializers.ValidationError("任务标题不能超过 120 个字符。")
        return value

    def validate_task_type(self, value):
        value = (value or "general").strip().lower()
        return value or "general"

    def validate_prompt(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("任务说明不能为空。")
        if len(value) > 8000:
            raise serializers.ValidationError("任务说明不能超过 8000 个字符。")
        return value


class AssistantLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantLog
        fields = ["id", "assistant", "level", "source", "message", "created_at"]
        read_only_fields = fields


class DeviceBindingSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    can_pair = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeviceBinding
        fields = [
            "id",
            "public_device_id",
            "name",
            "device_type",
            "status",
            "pairing_code_expires_at",
            "pairing_attempts",
            "paired_at",
            "revoked_at",
            "last_seen_at",
            "metadata",
            "is_active",
            "can_pair",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "public_device_id",
            "status",
            "pairing_code_expires_at",
            "pairing_attempts",
            "paired_at",
            "revoked_at",
            "last_seen_at",
            "is_active",
            "can_pair",
            "created_at",
            "updated_at",
        ]


class LocalAgentSerializer(serializers.ModelSerializer):
    device = DeviceBindingSerializer(read_only=True)
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = LocalAgent
        fields = [
            "id",
            "device",
            "version",
            "transport",
            "status",
            "last_heartbeat_at",
            "capabilities",
            "metadata",
            "is_online",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class WorkspaceBindingSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = WorkspaceBinding
        fields = [
            "id",
            "public_workspace_id",
            "assistant",
            "device",
            "mode",
            "display_name",
            "local_path_hint",
            "git_remote_url",
            "status",
            "policy",
            "last_indexed_at",
            "revoked_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "public_workspace_id", "status", "last_indexed_at", "revoked_at", "is_active", "created_at", "updated_at"]


class CreateDevicePairingCodeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    device_type = serializers.ChoiceField(choices=DeviceBinding.DeviceType.choices, default=DeviceBinding.DeviceType.DESKTOP)
    metadata = serializers.JSONField(required=False)

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Device name cannot be empty.")
        return value


class CompleteDevicePairingSerializer(serializers.Serializer):
    public_device_id = serializers.UUIDField()
    pairing_code = serializers.CharField(min_length=8, max_length=16)
    agent_version = serializers.CharField(max_length=32, required=False, allow_blank=True)
    transport = serializers.ChoiceField(choices=LocalAgent.Transport.choices, default=LocalAgent.Transport.WEBSOCKET)
    capabilities = serializers.JSONField(required=False)
    metadata = serializers.JSONField(required=False)

    def validate_pairing_code(self, value):
        value = (value or "").strip().upper().replace("-", "")
        if not value.isalnum():
            raise serializers.ValidationError("Pairing code can only contain letters and numbers.")
        return value


class AssistantSerializer(serializers.ModelSerializer):
    tools = AssistantToolProfileSerializer(required=False)
    storage = AssistantStorageSerializer(read_only=True)

    class Meta:
        model = Assistant
        fields = [
            "id",
            "name",
            "scene",
            "goal",
            "tone",
            "model_name",
            "status",
            "workspace_path",
            "tools",
            "storage",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "workspace_path", "created_at", "updated_at"]

    def create(self, validated_data):
        tools_data = validated_data.pop("tools", {})
        assistant = Assistant.objects.create(owner=self.context["request"].user, **validated_data)
        AssistantToolProfile.objects.create(assistant=assistant, **tools_data)
        return assistant

    def update(self, instance, validated_data):
        tools_data = validated_data.pop("tools", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tools_data is not None:
            tools, _ = AssistantToolProfile.objects.get_or_create(assistant=instance)
            for attr, value in tools_data.items():
                setattr(tools, attr, value)
            tools.approval_required = tools.code_enabled or tools.cron_enabled
            tools.save()
        return instance


class ProvisionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProvisionRequest
        fields = ["id", "assistant", "status", "admin_note", "created_at", "reviewed_at"]
        read_only_fields = ["id", "status", "admin_note", "created_at", "reviewed_at"]


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "code",
            "name",
            "description",
            "monthly_price_cents",
            "assistant_limit",
            "task_limit_monthly",
            "storage_limit_mb",
            "memory_enabled",
            "advanced_tools_enabled",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ["status", "plan", "current_period_start", "current_period_end"]


class UsageMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageMeter
        fields = ["period", "task_count", "tool_call_count", "storage_used_mb", "premium_model_call_count"]


class UserSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "subscription"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已被占用。")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "两次输入的密码不一致。"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        starter = Plan.objects.filter(code="starter", is_active=True).first()
        if starter:
            Subscription.objects.create(user=user, plan=starter)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(request=request, username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("用户名或密码错误。")
        if not user.is_active:
            raise serializers.ValidationError("账户已被禁用。")
        attrs["user"] = user
        return attrs


class RequestEmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class VerifyEmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_email(self, value):
        value = value.strip().lower()
        validate_email(value)
        return value

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("验证码必须是 6 位数字。")
        return value
