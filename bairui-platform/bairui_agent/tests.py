import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from .cli import main
from .client import default_capabilities, derive_ws_base, normalize_api_base, pair_device
from .config import AgentConfig, load_config, save_config
from .workspace import authorize_workspace, index_workspace


class AgentClientTests(TestCase):
    def test_normalize_api_base(self):
        self.assertEqual(normalize_api_base("http://127.0.0.1:8081"), "http://127.0.0.1:8081/portal-api/")
        self.assertEqual(normalize_api_base("http://127.0.0.1:8081/portal-api/"), "http://127.0.0.1:8081/portal-api/")

    def test_derive_ws_base(self):
        self.assertEqual(derive_ws_base("http://127.0.0.1:8081/portal-api/"), "ws://127.0.0.1:8081")
        self.assertEqual(derive_ws_base("https://api.example.com/portal-api/"), "wss://api.example.com")

    def test_save_and_load_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            config = AgentConfig(
                api_base_url="http://127.0.0.1:8081/portal-api/",
                ws_base_url="ws://127.0.0.1:8081",
                public_device_id="device-id",
                agent_token="secret-token",
                device_name="Local",
                workspace_path="C:/project",
                workspace_policy={"max_entries": 100},
            )

            save_config(config, path)
            loaded = load_config(path)

            self.assertEqual(loaded.public_device_id, "device-id")
            self.assertEqual(loaded.agent_token, "secret-token")
            self.assertEqual(loaded.workspace_path, "C:/project")
            self.assertEqual(loaded.workspace_policy["max_entries"], 100)

    def test_pair_device_builds_config_from_api_response(self):
        response = {
            "device": {"public_device_id": "public-id", "name": "Owner Laptop"},
            "agent_token": "token-123",
        }
        with patch("bairui_agent.client._post_json", return_value=response) as post_json:
            config = pair_device("http://127.0.0.1:8081", "public-id", "PAIR1234")

        post_json.assert_called_once()
        url, payload = post_json.call_args.args
        self.assertEqual(url, "http://127.0.0.1:8081/portal-api/agent/pair-device/")
        self.assertEqual(payload["public_device_id"], "public-id")
        self.assertEqual(config.ws_base_url, "ws://127.0.0.1:8081")
        self.assertEqual(config.agent_token, "token-123")

    def test_authorize_workspace_and_index_skips_sensitive_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("ok", encoding="utf-8")
            (root / ".env").write_text("SECRET=1", encoding="utf-8")
            (root / "private.pem").write_text("key", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "pkg.js").write_text("pkg", encoding="utf-8")
            (root / "large.bin").write_bytes(b"x" * 20)
            config = AgentConfig(
                api_base_url="http://127.0.0.1:8081/portal-api/",
                ws_base_url="ws://127.0.0.1:8081",
                public_device_id="device-id",
                agent_token="secret-token",
            )

            authorize_workspace(config, root, {"max_file_size_bytes": 10})
            result = index_workspace(config)

        paths = {entry["path"] for entry in result["entries"]}
        skipped = {item["path"]: item["reason"] for item in result["skipped"]}
        self.assertIn("src/app.py", paths)
        self.assertEqual(skipped[".env"], "sensitive_pattern")
        self.assertEqual(skipped["private.pem"], "sensitive_pattern")
        self.assertEqual(skipped["node_modules"], "excluded_dir")
        self.assertEqual(skipped["large.bin"], "file_too_large")

    def test_default_capabilities_include_workspace_index_when_authorized(self):
        config = AgentConfig(
            api_base_url="http://127.0.0.1:8081/portal-api/",
            ws_base_url="ws://127.0.0.1:8081",
            public_device_id="device-id",
            agent_token="secret-token",
            workspace_path="C:/project",
        )

        self.assertTrue(default_capabilities(config)["workspace_index"])

    def test_cli_status_hides_token(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "api_base_url": "http://127.0.0.1:8081/portal-api/",
                        "ws_base_url": "ws://127.0.0.1:8081",
                        "public_device_id": "public-id",
                        "agent_token": "secret-token",
                        "device_name": "Local",
                        "workspace_path": "",
                        "workspace_policy": {},
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                code = main(["--config", str(path), "status"])

        self.assertEqual(code, 0)
        self.assertIn("agent_token: <hidden>", output.getvalue())
        self.assertNotIn("secret-token", output.getvalue())

    def test_cli_authorize_persists_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir()
            save_config(
                AgentConfig(
                    api_base_url="http://127.0.0.1:8081/portal-api/",
                    ws_base_url="ws://127.0.0.1:8081",
                    public_device_id="device-id",
                    agent_token="secret-token",
                ),
                config_path,
            )
            output = io.StringIO()

            with redirect_stdout(output):
                code = main(["--config", str(config_path), "authorize", str(workspace), "--max-entries", "25"])

            loaded = load_config(config_path)

        self.assertEqual(code, 0)
        self.assertEqual(Path(loaded.workspace_path), workspace.resolve())
        self.assertEqual(loaded.workspace_policy["max_entries"], 25)
        self.assertIn("workspace authorized", output.getvalue())
