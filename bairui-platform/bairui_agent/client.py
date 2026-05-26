import json
import platform
import asyncio
from urllib import error, request
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

import websockets

from . import __version__
from .config import AgentConfig


def normalize_api_base(url):
    url = url.rstrip("/") + "/"
    if not url.endswith("portal-api/"):
        url = urljoin(url, "portal-api/")
    return url


def derive_ws_base(api_base_url):
    parsed = urlparse(api_base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse((scheme, parsed.netloc, "", "", "", "")).rstrip("/")


def pair_device(api_base_url, public_device_id, pairing_code, device_name=""):
    api_base_url = normalize_api_base(api_base_url)
    payload = {
        "public_device_id": public_device_id,
        "pairing_code": pairing_code,
        "agent_version": __version__,
        "transport": "websocket",
        "capabilities": default_capabilities(),
        "metadata": default_metadata(),
    }
    data = _post_json(urljoin(api_base_url, "agent/pair-device/"), payload)
    return AgentConfig(
        api_base_url=api_base_url,
        ws_base_url=derive_ws_base(api_base_url),
        public_device_id=data["device"]["public_device_id"],
        agent_token=data["agent_token"],
        device_name=device_name or data["device"].get("name", ""),
    )


async def send_heartbeat(config):
    query = urlencode({"device_id": config.public_device_id, "token": config.agent_token})
    url = f"{config.ws_base_url}/ws/agent/status/?{query}"
    async with websockets.connect(url) as websocket:
        connected = json.loads(await websocket.recv())
        await websocket.send(
            json.dumps(
                {
                    "type": "heartbeat",
                    "agent_version": __version__,
                    "capabilities": default_capabilities(config),
                    "metadata": default_metadata(),
                }
            )
        )
        ack = json.loads(await websocket.recv())
        return connected, ack


async def run_heartbeat_loop(config, interval_seconds):
    while True:
        try:
            connected, ack = await send_heartbeat(config)
            print(f"heartbeat ok: {ack.get('last_heartbeat_at')} status={ack.get('agent_status')}")
        except Exception as exc:
            print(f"heartbeat failed: {exc}")
        await asyncio.sleep(interval_seconds)


def default_capabilities(config=None):
    return {
        "filesystem": "read_only",
        "shell": "disabled",
        "workspace_index": bool(getattr(config, "workspace_path", "")),
    }


def default_metadata():
    return {
        "platform": platform.system().lower(),
        "platform_release": platform.release(),
        "python": platform.python_version(),
    }


def _post_json(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
