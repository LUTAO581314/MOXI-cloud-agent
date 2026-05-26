from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase

from .consumers import AgentStatusConsumer
from .models import DeviceBinding, LocalAgent


class AgentStatusWebsocketTests(TestCase):
    def test_agent_token_authentication_accepts_active_device(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        token = "agent-token-123"
        device = DeviceBinding.objects.create(
            user=user,
            name="Owner Laptop",
            status=DeviceBinding.Status.ACTIVE,
            agent_token_hash=make_password(token),
        )
        consumer = AgentStatusConsumer()

        authenticated = async_to_sync(consumer._authenticate_device)(str(device.public_device_id), token)
        rejected = async_to_sync(consumer._authenticate_device)(str(device.public_device_id), "wrong-token")

        self.assertEqual(authenticated.id, device.id)
        self.assertIsNone(rejected)

    def test_agent_heartbeat_updates_online_status(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        device = DeviceBinding.objects.create(
            user=user,
            name="Owner Laptop",
            status=DeviceBinding.Status.ACTIVE,
            agent_token_hash=make_password("agent-token-123"),
        )
        LocalAgent.objects.create(device=device, status=LocalAgent.Status.OFFLINE)
        consumer = AgentStatusConsumer()

        agent = async_to_sync(consumer._heartbeat)(
            device,
            capabilities={"filesystem": "read_only"},
            metadata={"platform": "windows"},
            version="0.1.0",
        )

        device.refresh_from_db()
        agent.refresh_from_db()
        self.assertIsNotNone(device.last_seen_at)
        self.assertEqual(agent.status, LocalAgent.Status.ONLINE)
        self.assertEqual(agent.transport, LocalAgent.Transport.WEBSOCKET)
        self.assertEqual(agent.version, "0.1.0")
        self.assertEqual(agent.capabilities["filesystem"], "read_only")
        self.assertEqual(agent.metadata["platform"], "windows")

    def test_agent_disconnect_marks_offline(self):
        user = get_user_model().objects.create_user(username="owner", password="strong-pass-123")
        device = DeviceBinding.objects.create(user=user, name="Owner Laptop", status=DeviceBinding.Status.ACTIVE)
        LocalAgent.objects.create(device=device, status=LocalAgent.Status.ONLINE)
        consumer = AgentStatusConsumer()

        async_to_sync(consumer._mark_agent_offline)(device)

        device.local_agent.refresh_from_db()
        self.assertEqual(device.local_agent.status, LocalAgent.Status.OFFLINE)

    def test_websocket_route_is_registered(self):
        from assistants.routing import websocket_urlpatterns

        self.assertEqual(websocket_urlpatterns[0].pattern._route, "ws/agent/status/")
