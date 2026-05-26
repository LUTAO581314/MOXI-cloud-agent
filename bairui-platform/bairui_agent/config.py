import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".bairui-agent" / "config.json"


@dataclass
class AgentConfig:
    api_base_url: str
    ws_base_url: str
    public_device_id: str
    agent_token: str
    device_name: str = ""
    workspace_path: str = ""
    workspace_policy: dict | None = None

    def __post_init__(self):
        if self.workspace_policy is None:
            self.workspace_policy = {}


def load_config(path=None):
    config_path = Path(path or os.getenv("BAIRUI_AGENT_CONFIG") or DEFAULT_CONFIG_PATH)
    if not config_path.exists():
        raise FileNotFoundError(f"Agent config not found: {config_path}")
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return AgentConfig(**data)


def save_config(config, path=None):
    config_path = Path(path or os.getenv("BAIRUI_AGENT_CONFIG") or DEFAULT_CONFIG_PATH)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
    return config_path
