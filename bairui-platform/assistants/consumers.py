import json
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.hashers import check_password
from django.utils import timezone

from .models import DeviceBinding, LocalAgent


class AgentStatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.device = None
        query = parse_qs(self.scope.get("query_string", b"").decode("utf-8"))
        device_id = (query.get("device_id") or [""])[0]
        token = (query.get("token") or [""])[0]
        device = await self._authenticate_device(device_id, token)
        if device is None:
            raise DenyConnection("Invalid agent credentials.")

        self.device = device
        await self.accept()
        agent = await self._mark_agent_online(device)
        await self.send_json(
            {
                "type": "connected",
                "device_id": str(device.public_device_id),
                "agent_status": agent.status,
                "server_time": timezone.now().isoformat(),
            }
        )

    async def disconnect(self, close_code):
        if self.device is not None:
            await self._mark_agent_offline(self.device)

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")
        if message_type == "heartbeat":
            agent = await self._heartbeat(
                self.device,
                capabilities=content.get("capabilities"),
                metadata=content.get("metadata"),
                version=content.get("agent_version"),
            )
            await self.send_json(
                {
                    "type": "heartbeat_ack",
                    "agent_status": agent.status,
                    "last_heartbeat_at": agent.last_heartbeat_at.isoformat(),
                }
            )
            return

        await self.send_json({"type": "error", "message": "Unsupported message type."})

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if text_data is None:
            await self.send_json({"type": "error", "message": "Only JSON text messages are supported."})
            return
        try:
            content = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "Invalid JSON."})
            return
        await self.receive_json(content)

    @sync_to_async
    def _authenticate_device(self, public_device_id, token):
        if not public_device_id or not token:
            return None
        device = (
            DeviceBinding.objects.filter(
                public_device_id=public_device_id,
                status=DeviceBinding.Status.ACTIVE,
                revoked_at__isnull=True,
            )
            .select_related("user")
            .first()
        )
        if device is None or not device.agent_token_hash:
            return None
        if not check_password(token, device.agent_token_hash):
            return None
        return device

    @sync_to_async
    def _mark_agent_online(self, device):
        now = timezone.now()
        device.last_seen_at = now
        device.save(update_fields=["last_seen_at", "updated_at"])
        agent, _ = LocalAgent.objects.get_or_create(device=device)
        agent.status = LocalAgent.Status.ONLINE
        agent.last_heartbeat_at = now
        agent.transport = LocalAgent.Transport.WEBSOCKET
        agent.save(update_fields=["status", "last_heartbeat_at", "transport", "updated_at"])
        return agent

    @sync_to_async
    def _mark_agent_offline(self, device):
        LocalAgent.objects.filter(device=device).update(status=LocalAgent.Status.OFFLINE, updated_at=timezone.now())

    @sync_to_async
    def _heartbeat(self, device, capabilities=None, metadata=None, version=None):
        now = timezone.now()
        device.last_seen_at = now
        device.save(update_fields=["last_seen_at", "updated_at"])
        agent, _ = LocalAgent.objects.get_or_create(device=device)
        agent.status = LocalAgent.Status.ONLINE
        agent.transport = LocalAgent.Transport.WEBSOCKET
        agent.last_heartbeat_at = now
        if isinstance(capabilities, dict):
            agent.capabilities = capabilities
        if isinstance(metadata, dict):
            agent.metadata = metadata
        if version:
            agent.version = str(version)[:32]
        agent.save(update_fields=["status", "transport", "last_heartbeat_at", "capabilities", "metadata", "version", "updated_at"])
        return agent
