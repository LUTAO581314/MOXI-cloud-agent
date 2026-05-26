from django.contrib import admin

from .models import (
    Assistant,
    AssistantLog,
    AssistantFile,
    AssistantStorage,
    AssistantTask,
    AssistantToolProfile,
    AuditEvent,
    DeviceBinding,
    EmailLoginCode,
    InvitationCode,
    LocalAgent,
    MemoryItem,
    Plan,
    ProvisionRequest,
    RuntimeBinding,
    Subscription,
    UsageMeter,
    WorkspaceBinding,
)


class AssistantToolProfileInline(admin.StackedInline):
    model = AssistantToolProfile
    extra = 0


class RuntimeBindingInline(admin.StackedInline):
    model = RuntimeBinding
    extra = 0


class AssistantStorageInline(admin.StackedInline):
    model = AssistantStorage
    extra = 0
    readonly_fields = ("available_mb",)


class AssistantFileInline(admin.TabularInline):
    model = AssistantFile
    extra = 0
    readonly_fields = ("original_name", "stored_name", "path", "size_bytes", "size_mb", "content_type", "uploaded_by", "created_at")
    can_delete = False


class WorkspaceBindingInline(admin.TabularInline):
    model = WorkspaceBinding
    extra = 0
    readonly_fields = ("public_workspace_id", "created_at", "updated_at")
    fields = ("display_name", "mode", "status", "device", "public_workspace_id", "created_at")


@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "scene", "model_name", "status", "updated_at")
    list_filter = ("scene", "status", "model_name")
    search_fields = ("name", "owner__username", "goal")
    inlines = [AssistantToolProfileInline, RuntimeBindingInline, AssistantStorageInline, AssistantFileInline, WorkspaceBindingInline]


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "monthly_price_cents", "assistant_limit", "is_active")
    list_filter = ("is_active", "memory_enabled", "advanced_tools_enabled")
    search_fields = ("name", "code", "description")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "current_period_end", "updated_at")
    list_filter = ("status", "plan")
    search_fields = ("user__username", "user__email", "plan__name")


@admin.register(UsageMeter)
class UsageMeterAdmin(admin.ModelAdmin):
    list_display = ("user", "period", "task_count", "tool_call_count", "storage_used_mb")
    list_filter = ("period",)
    search_fields = ("user__username", "user__email")


@admin.register(ProvisionRequest)
class ProvisionRequestAdmin(admin.ModelAdmin):
    list_display = ("assistant", "user", "status", "created_at", "reviewed_at")
    list_filter = ("status", "created_at")
    search_fields = ("assistant__name", "user__username", "admin_note")


@admin.register(AssistantTask)
class AssistantTaskAdmin(admin.ModelAdmin):
    list_display = ("assistant", "title", "task_type", "status", "progress", "updated_at")
    list_filter = ("status", "task_type")
    search_fields = ("assistant__name", "title", "prompt", "result_summary")


@admin.register(AssistantLog)
class AssistantLogAdmin(admin.ModelAdmin):
    list_display = ("assistant", "level", "source", "created_at")
    list_filter = ("level", "source")
    search_fields = ("assistant__name", "message")


@admin.register(DeviceBinding)
class DeviceBindingAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "device_type", "status", "last_seen_at", "updated_at")
    list_filter = ("device_type", "status", "created_at")
    search_fields = ("name", "user__username", "user__email", "public_device_id")
    readonly_fields = ("public_device_id", "created_at", "updated_at")


@admin.register(LocalAgent)
class LocalAgentAdmin(admin.ModelAdmin):
    list_display = ("device", "version", "transport", "status", "last_heartbeat_at", "updated_at")
    list_filter = ("transport", "status")
    search_fields = ("device__name", "device__user__username", "version")


@admin.register(WorkspaceBinding)
class WorkspaceBindingAdmin(admin.ModelAdmin):
    list_display = ("display_name", "owner", "mode", "status", "assistant", "device", "updated_at")
    list_filter = ("mode", "status", "created_at")
    search_fields = ("display_name", "owner__username", "owner__email", "assistant__name", "git_remote_url", "local_path_hint")
    readonly_fields = ("public_workspace_id", "created_at", "updated_at")


@admin.register(MemoryItem)
class MemoryItemAdmin(admin.ModelAdmin):
    list_display = ("assistant", "kind", "created_at")
    list_filter = ("kind",)
    search_fields = ("assistant__name", "content")


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "plan", "redemption_count", "max_redemptions", "is_active", "expires_at")
    list_filter = ("is_active", "plan")
    search_fields = ("code",)


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_type", "target_id", "created_at")
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("actor__username", "action", "target_type", "target_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(EmailLoginCode)
class EmailLoginCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "expires_at", "consumed_at", "attempts", "created_at")
    list_filter = ("consumed_at", "created_at")
    search_fields = ("email", "ip_address")
    readonly_fields = ("code_hash", "created_at", "updated_at")
