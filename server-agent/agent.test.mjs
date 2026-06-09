import test from "node:test";
import assert from "node:assert/strict";
import { HEARTBEAT_PROTOCOL_VERSION } from "../packages/server-protocol/index.mjs";
import { fetchHermesHeartbeat, loadAgentConfig, postHeartbeat, runOnce } from "./index.mjs";

const heartbeat = {
  protocol_version: HEARTBEAT_PROTOCOL_VERSION,
  server_id: "srv_1",
  organization_id: "org_1",
  license_id: "lic_1",
  license_status: "valid",
  hermes_version: "0.1.0",
  health_status: "ok",
  database_status: "ready",
  backup_status: "not_configured",
  connector_status_summary: {},
  error_count_24h: 0,
  brand_key: "bairui",
  created_at: "2026-06-10T00:00:00.000Z"
};

function jsonResponse(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body
  };
}

test("loads server-agent config from environment", () => {
  const config = loadAgentConfig({
    BAIRUI_HERMES_HEARTBEAT_URL: "http://hermes.local/platform/heartbeat",
    BAIRUI_PLATFORM_HEARTBEAT_URL: "https://platform.local/api/server-heartbeat",
    BAIRUI_SERVER_AGENT_TOKEN: "token",
    BAIRUI_SERVER_AGENT_TIMEOUT_MS: "5000"
  });
  assert.equal(config.hermesHeartbeatUrl, "http://hermes.local/platform/heartbeat");
  assert.equal(config.platformHeartbeatUrl, "https://platform.local/api/server-heartbeat");
  assert.equal(config.agentToken, "token");
  assert.equal(config.timeoutMs, 5000);
});

test("fetches and validates Hermes heartbeat", async () => {
  const config = loadAgentConfig({});
  const result = await fetchHermesHeartbeat(config, async () => jsonResponse({ heartbeat }));
  assert.equal(result.server_id, "srv_1");
});

test("posts heartbeat with bearer token when configured", async () => {
  const config = loadAgentConfig({
    BAIRUI_PLATFORM_HEARTBEAT_URL: "https://platform.local/api/server-heartbeat",
    BAIRUI_SERVER_AGENT_TOKEN: "token"
  });
  let request;
  await postHeartbeat(config, heartbeat, async (url, options) => {
    request = { url, options };
    return jsonResponse({ accepted: true });
  });
  assert.equal(request.url, "https://platform.local/api/server-heartbeat");
  assert.equal(request.options.headers.authorization, "Bearer token");
  assert.deepEqual(JSON.parse(request.options.body), { heartbeat });
});

test("runs one outbound heartbeat cycle", async () => {
  const config = loadAgentConfig({
    BAIRUI_PLATFORM_HEARTBEAT_URL: "https://platform.local/api/server-heartbeat"
  });
  const calls = [];
  const result = await runOnce(config, async (url) => {
    calls.push(url);
    if (url === config.hermesHeartbeatUrl) {
      return jsonResponse({ heartbeat });
    }
    return jsonResponse({ accepted: true });
  });
  assert.equal(calls.length, 2);
  assert.equal(result.heartbeat.server_id, "srv_1");
  assert.equal(result.result.accepted, true);
});
