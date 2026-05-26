from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from pathlib import Path
from tempfile import TemporaryDirectory
from rest_framework.test import APIClient

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


class PlatformApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.starter = Plan.objects.create(
            code="starter",
            name="Starter",
            assistant_limit=1,
            task_limit_monthly=100,
            storage_limit_mb=512,
        )

    def test_register_creates_subscription_and_session(self):
        response = self.client.post(
            "/portal-api/auth/register/",
            {
                "username": "owner",
                "email": "owner@example.com",
                "password": "strong-pass-123",
                "password_confirm": "strong-pass-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Subscription.objects.filter(user__username="owner", plan=self.starter).exists())
        me = self.client.get("/portal-api/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["username"], "owner")

    def test_user_can_create_assistant_and_submit_provision_request(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        Subscription.objects.create(user=user, plan=self.starter)
        self.client.force_authenticate(user=user)

        assistant_response = self.client.post(
            "/portal-api/assistants/",
            {
                "name": "财务分析助手",
                "scene": "research",
                "goal": "解析企业财报",
                "tone": "研究型",
                "model_name": "gpt-5.5",
                "tools": {"browser_enabled": True, "files_enabled": True},
            },
            format="json",
        )
        self.assertEqual(assistant_response.status_code, 201)

        provision_response = self.client.post(
            "/portal-api/provision-requests/",
            {"assistant": assistant_response.data["id"]},
            format="json",
        )
        self.assertEqual(provision_response.status_code, 201)
        self.assertEqual(Assistant.objects.get(id=assistant_response.data["id"]).status, Assistant.Status.PENDING)

    def test_plan_assistant_limit_is_enforced(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        Subscription.objects.create(user=user, plan=self.starter)
        Assistant.objects.create(owner=user, name="现有助理")
        self.client.force_authenticate(user=user)

        response = self.client.post("/portal-api/assistants/", {"name": "第二个助理"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("plan", response.data)

    def test_admin_can_approve_provision_request(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        admin = get_user_model().objects.create_user(username="admin", password="strong-pass-123", is_staff=True)
        assistant = Assistant.objects.create(owner=user, name="财务分析助手", status=Assistant.Status.PENDING)
        provision = ProvisionRequest.objects.create(user=user, assistant=assistant)
        self.client.force_authenticate(user=admin)

        response = self.client.post(f"/portal-api/provision-requests/{provision.id}/approve/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        assistant.refresh_from_db()
        provision.refresh_from_db()
        self.assertEqual(assistant.status, Assistant.Status.ACTIVE)
        self.assertEqual(provision.status, ProvisionRequest.Status.APPROVED)
        self.assertTrue(assistant.workspace_path)

    def test_approval_allocates_storage_from_user_plan(self):
        with TemporaryDirectory() as storage_root, override_settings(ASSISTANT_STORAGE_ROOT=storage_root):
            pro = Plan.objects.create(
                code="pro",
                name="Pro",
                assistant_limit=5,
                storage_limit_mb=5120,
            )
            user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
            admin = get_user_model().objects.create_user(username="admin", password="strong-pass-123", is_staff=True)
            Subscription.objects.create(user=user, plan=pro)
            assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.PENDING)
            provision = ProvisionRequest.objects.create(user=user, assistant=assistant)
            self.client.force_authenticate(user=admin)

            response = self.client.post(f"/portal-api/provision-requests/{provision.id}/approve/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        storage = AssistantStorage.objects.get(assistant=assistant)
        assistant.refresh_from_db()
        self.assertEqual(storage.quota_mb, 5120)
        self.assertEqual(assistant.workspace_path, storage.workspace_path)
        self.assertTrue(storage.files_path.endswith("/files"))
        self.assertTrue(storage.memory_path.endswith("/memory"))
        self.assertTrue(storage.logs_path.endswith("/logs"))
        self.assertNotEqual(storage.files_path, storage.memory_path)

    def test_upload_file_uses_storage_quota_and_records_metadata(self):
        with TemporaryDirectory() as storage_root, override_settings(ASSISTANT_STORAGE_ROOT=storage_root):
            user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
            assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.ACTIVE)
            storage = AssistantStorage.objects.create(
                assistant=assistant,
                quota_mb=2,
                root_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}",
                workspace_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/workspace",
                files_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/files",
                memory_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/memory",
                logs_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/logs",
            )
            self.client.force_authenticate(user=user)
            upload = SimpleUploadedFile("report.txt", b"hello bairui", content_type="text/plain")

            response = self.client.post(f"/portal-api/assistants/{assistant.id}/upload_file/", {"file": upload}, format="multipart")

            self.assertEqual(response.status_code, 201)
            storage.refresh_from_db()
            file_record = AssistantFile.objects.get(assistant=assistant)
            self.assertEqual(storage.used_mb, 1)
            self.assertEqual(file_record.original_name, "report.txt")
            self.assertTrue(Path(file_record.path).resolve().is_relative_to(Path(storage.files_path).resolve()))

    def test_upload_file_rejects_when_quota_exceeded(self):
        with TemporaryDirectory() as storage_root, override_settings(ASSISTANT_STORAGE_ROOT=storage_root):
            user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
            assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.ACTIVE)
            AssistantStorage.objects.create(
                assistant=assistant,
                quota_mb=1,
                used_mb=1,
                root_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}",
                workspace_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/workspace",
                files_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/files",
                memory_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/memory",
                logs_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/logs",
            )
            self.client.force_authenticate(user=user)
            upload = SimpleUploadedFile("report.txt", b"hello bairui", content_type="text/plain")

            response = self.client.post(f"/portal-api/assistants/{assistant.id}/upload_file/", {"file": upload}, format="multipart")

            self.assertEqual(response.status_code, 400)
            self.assertFalse(AssistantFile.objects.filter(assistant=assistant).exists())

    def test_memory_item_requires_plan_and_tool_enabled_then_writes_jsonl(self):
        with TemporaryDirectory() as storage_root, override_settings(ASSISTANT_STORAGE_ROOT=storage_root):
            memory_plan = Plan.objects.create(
                code="memory",
                name="Memory",
                assistant_limit=3,
                storage_limit_mb=512,
                memory_enabled=True,
            )
            user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
            Subscription.objects.create(user=user, plan=memory_plan)
            assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.ACTIVE)
            AssistantToolProfile.objects.create(assistant=assistant, memory_enabled=True)
            storage = AssistantStorage.objects.create(
                assistant=assistant,
                quota_mb=512,
                root_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}",
                workspace_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/workspace",
                files_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/files",
                memory_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/memory",
                logs_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/logs",
            )
            self.client.force_authenticate(user=user)

            response = self.client.post(
                f"/portal-api/assistants/{assistant.id}/memory/",
                {"kind": "preference", "content": "主人偏好用中文输出简洁结论。"},
                format="json",
            )

            self.assertEqual(response.status_code, 201)
            self.assertTrue(MemoryItem.objects.filter(assistant=assistant, kind="preference").exists())
            memory_log = Path(storage.memory_path) / "memory_items.jsonl"
            self.assertTrue(memory_log.exists())
            self.assertIn("主人偏好用中文输出简洁结论", memory_log.read_text(encoding="utf-8"))

    def test_memory_item_rejects_when_plan_does_not_allow_memory(self):
        with TemporaryDirectory() as storage_root, override_settings(ASSISTANT_STORAGE_ROOT=storage_root):
            user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
            Subscription.objects.create(user=user, plan=self.starter)
            assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.ACTIVE)
            AssistantToolProfile.objects.create(assistant=assistant, memory_enabled=True)
            AssistantStorage.objects.create(
                assistant=assistant,
                quota_mb=512,
                root_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}",
                workspace_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/workspace",
                files_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/files",
                memory_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/memory",
                logs_path=f"{storage_root}/user-{user.id}/assistant-{assistant.id}/logs",
            )
            self.client.force_authenticate(user=user)

            response = self.client.post(
                f"/portal-api/assistants/{assistant.id}/memory/",
                {"kind": "note", "content": "这条记忆不应该保存。"},
                format="json",
            )

            self.assertEqual(response.status_code, 400)
            self.assertFalse(MemoryItem.objects.filter(assistant=assistant).exists())

    def test_user_can_create_task_for_active_assistant_and_usage_is_counted(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        Subscription.objects.create(user=user, plan=self.starter)
        assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.ACTIVE)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            f"/portal-api/assistants/{assistant.id}/tasks/",
            {
                "title": "整理财报摘要",
                "task_type": "analysis",
                "prompt": "请把上传的财报整理成三段摘要。",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        task = AssistantTask.objects.get(assistant=assistant)
        self.assertEqual(task.created_by, user)
        self.assertEqual(task.status, AssistantTask.Status.QUEUED)
        self.assertEqual(UsageMeter.objects.get(user=user).task_count, 1)

    def test_task_creation_rejects_inactive_assistant(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        Subscription.objects.create(user=user, plan=self.starter)
        assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.PENDING)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            f"/portal-api/assistants/{assistant.id}/tasks/",
            {"title": "不能执行", "task_type": "analysis", "prompt": "这条任务不应该创建。"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(AssistantTask.objects.filter(assistant=assistant).exists())

    def test_task_creation_respects_monthly_plan_limit(self):
        limited = Plan.objects.create(code="limited", name="Limited", task_limit_monthly=1, assistant_limit=1)
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        Subscription.objects.create(user=user, plan=limited)
        assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.ACTIVE)
        UsageMeter.objects.create(user=user, period="2026-05", task_count=1)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            f"/portal-api/assistants/{assistant.id}/tasks/",
            {"title": "超额任务", "task_type": "analysis", "prompt": "这条任务不应该创建。"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(AssistantTask.objects.filter(assistant=assistant).exists())

    def test_user_can_list_own_assistant_logs_newest_first(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        assistant = Assistant.objects.create(owner=user, name="研究助理", status=Assistant.Status.ACTIVE)
        old = AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.INFO, source="platform", message="旧日志")
        new = AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.WARNING, source="tasks", message="新日志")
        self.client.force_authenticate(user=user)

        response = self.client.get(f"/portal-api/assistants/{assistant.id}/logs/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [new.id, old.id])
        self.assertEqual(response.data[0]["message"], "新日志")

    def test_user_cannot_list_another_users_assistant_logs(self):
        owner = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        other = get_user_model().objects.create_user(username="other", password="strong-pass-123")
        assistant = Assistant.objects.create(owner=owner, name="研究助理", status=Assistant.Status.ACTIVE)
        AssistantLog.objects.create(assistant=assistant, level=AssistantLog.Level.INFO, source="platform", message="私有日志")
        self.client.force_authenticate(user=other)

        response = self.client.get(f"/portal-api/assistants/{assistant.id}/logs/")

        self.assertEqual(response.status_code, 404)

    def test_device_binding_and_local_agent_status_helpers(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        device = DeviceBinding.objects.create(
            user=user,
            name="Owner Windows Workbench",
            device_type=DeviceBinding.DeviceType.DESKTOP,
            status=DeviceBinding.Status.ACTIVE,
        )
        agent = LocalAgent.objects.create(
            device=device,
            version="0.1.0",
            transport=LocalAgent.Transport.WEBSOCKET,
            status=LocalAgent.Status.ONLINE,
            capabilities={"filesystem": "read_only", "shell": "confirm_required"},
        )

        self.assertTrue(device.public_device_id)
        self.assertTrue(device.is_active)
        self.assertTrue(agent.is_online)
        self.assertEqual(agent.capabilities["shell"], "confirm_required")

    def test_user_can_create_device_pairing_code(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        self.client.force_authenticate(user=user)

        response = self.client.post(
            "/portal-api/devices/pairing-code/",
            {"name": "Owner Laptop", "device_type": "desktop", "metadata": {"os": "windows"}},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Owner Laptop")
        self.assertEqual(len(response.data["pairing_code"]), 8)
        device = DeviceBinding.objects.get(user=user)
        self.assertTrue(device.can_pair)
        self.assertTrue(device.pairing_code_hash)
        self.assertEqual(device.metadata["os"], "windows")

    def test_pairing_code_can_activate_device_and_returns_agent_token_once(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        self.client.force_authenticate(user=user)
        create_response = self.client.post(
            "/portal-api/devices/pairing-code/",
            {"name": "Owner Laptop", "device_type": "desktop"},
            format="json",
        )
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/portal-api/agent/pair-device/",
            {
                "public_device_id": create_response.data["public_device_id"],
                "pairing_code": create_response.data["pairing_code"],
                "agent_version": "0.1.0",
                "transport": "websocket",
                "capabilities": {"filesystem": "read_only"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["agent_token"])
        device = DeviceBinding.objects.get(user=user)
        self.assertEqual(device.status, DeviceBinding.Status.ACTIVE)
        self.assertFalse(device.pairing_code_hash)
        self.assertTrue(device.agent_token_hash)
        agent = LocalAgent.objects.get(device=device)
        self.assertEqual(agent.version, "0.1.0")
        self.assertEqual(agent.capabilities["filesystem"], "read_only")

        replay = self.client.post(
            "/portal-api/agent/pair-device/",
            {
                "public_device_id": create_response.data["public_device_id"],
                "pairing_code": create_response.data["pairing_code"],
            },
            format="json",
        )
        self.assertEqual(replay.status_code, 400)

    def test_wrong_pairing_code_increments_attempts(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        self.client.force_authenticate(user=user)
        create_response = self.client.post(
            "/portal-api/devices/pairing-code/",
            {"name": "Owner Laptop", "device_type": "desktop"},
            format="json",
        )
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/portal-api/agent/pair-device/",
            {"public_device_id": create_response.data["public_device_id"], "pairing_code": "BADCODE1"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(DeviceBinding.objects.get(user=user).pairing_attempts, 1)

    def test_user_can_only_list_own_devices(self):
        owner = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        other = get_user_model().objects.create_user(username="other", password="strong-pass-123")
        DeviceBinding.objects.create(user=owner, name="Owner Laptop")
        DeviceBinding.objects.create(user=other, name="Other Laptop")
        self.client.force_authenticate(user=owner)

        response = self.client.get("/portal-api/devices/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Owner Laptop")

    def test_user_can_revoke_own_device(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        device = DeviceBinding.objects.create(
            user=user,
            name="Owner Laptop",
            status=DeviceBinding.Status.ACTIVE,
            agent_token_hash="token-hash",
        )
        LocalAgent.objects.create(device=device, status=LocalAgent.Status.ONLINE)
        self.client.force_authenticate(user=user)

        response = self.client.post(f"/portal-api/devices/{device.id}/revoke/")

        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertEqual(device.status, DeviceBinding.Status.REVOKED)
        self.assertFalse(device.agent_token_hash)
        self.assertEqual(device.local_agent.status, LocalAgent.Status.OFFLINE)

    def test_workspace_binding_accepts_owned_assistant_and_device(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        assistant = Assistant.objects.create(owner=user, name="Local Dev Assistant", status=Assistant.Status.ACTIVE)
        device = DeviceBinding.objects.create(user=user, name="Owner Laptop", status=DeviceBinding.Status.ACTIVE)
        workspace = WorkspaceBinding(
            owner=user,
            assistant=assistant,
            device=device,
            mode=WorkspaceBinding.Mode.LOCAL,
            display_name="Local project",
            local_path_hint="C:/Users/owner/project",
            policy={"allow_write": False, "sensitive_globs": [".env", "*.pem"]},
        )

        workspace.full_clean()
        workspace.save()

        self.assertTrue(workspace.public_workspace_id)
        self.assertTrue(workspace.is_active)
        self.assertEqual(workspace.policy["allow_write"], False)

    def test_workspace_binding_rejects_cross_user_assistant_or_device(self):
        owner = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        other = get_user_model().objects.create_user(username="other", password="strong-pass-123")
        foreign_assistant = Assistant.objects.create(owner=other, name="Other Assistant")
        foreign_device = DeviceBinding.objects.create(user=other, name="Other Laptop")

        workspace = WorkspaceBinding(
            owner=owner,
            assistant=foreign_assistant,
            device=foreign_device,
            mode=WorkspaceBinding.Mode.LOCAL,
            display_name="Invalid workspace",
            local_path_hint="C:/Users/owner/project",
        )

        with self.assertRaises(ValidationError) as context:
            workspace.full_clean()

        self.assertIn("assistant", context.exception.message_dict)
        self.assertIn("device", context.exception.message_dict)

    def test_workspace_binding_enforces_mode_specific_location_fields(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        local_workspace = WorkspaceBinding(
            owner=user,
            mode=WorkspaceBinding.Mode.LOCAL,
            display_name="Invalid local workspace",
            local_path_hint="C:/Users/owner/project",
            git_remote_url="https://example.com/repo.git",
        )
        git_workspace = WorkspaceBinding(
            owner=user,
            mode=WorkspaceBinding.Mode.GIT,
            display_name="Invalid git workspace",
            local_path_hint="C:/Users/owner/project",
            git_remote_url="https://example.com/repo.git",
        )

        with self.assertRaises(ValidationError) as local_context:
            local_workspace.full_clean()
        with self.assertRaises(ValidationError) as git_context:
            git_workspace.full_clean()

        self.assertIn("git_remote_url", local_context.exception.message_dict)
        self.assertIn("local_path_hint", git_context.exception.message_dict)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailCodeLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.starter = Plan.objects.create(code="starter", name="Starter")

    def test_request_email_code_sends_mail(self):
        response = self.client.post("/portal-api/auth/email-code/request/", {"email": "new@example.com"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("百瑞云代理登录验证码", mail.outbox[0].subject)
        self.assertTrue(EmailLoginCode.objects.filter(email="new@example.com").exists())

    def test_verify_email_code_creates_user_subscription_and_session(self):
        self.client.post("/portal-api/auth/email-code/request/", {"email": "new@example.com"}, format="json")
        body = mail.outbox[0].body
        code = "".join(ch for ch in body if ch.isdigit())[:6]

        response = self.client.post(
            "/portal-api/auth/email-code/verify/",
            {"email": "new@example.com", "code": code},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "new@example.com")
        self.assertTrue(Subscription.objects.filter(user__email="new@example.com", plan=self.starter).exists())
        me = self.client.get("/portal-api/auth/me/")
        self.assertEqual(me.status_code, 200)

    def test_wrong_email_code_increments_attempts(self):
        self.client.post("/portal-api/auth/email-code/request/", {"email": "new@example.com"}, format="json")

        response = self.client.post(
            "/portal-api/auth/email-code/verify/",
            {"email": "new@example.com", "code": "000000"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(EmailLoginCode.objects.get(email="new@example.com").attempts, 1)
