import test from "node:test";
import assert from "node:assert/strict";
import { HEARTBEAT_PROTOCOL_VERSION, buildHeartbeat, validateHeartbeat } from "./index.mjs";

test("builds a normalized heartbeat payload", () => {
  const heartbeat = buildHeartbeat({
    server_id: "srv_1",
    organization_id: "org_1",
    license_id: "lic_1",
    license_status: "valid",
    hermes_version: "0.1.0",
    health_status: "ok",
    database_status: "ready",
    connector_status_summary: { feishu: "missing_config" },
    error_count_24h: 2,
    brand_key: "bairui",
    created_at: "2026-06-10T00:00:00.000Z"
  });

  assert.equal(heartbeat.protocol_version, HEARTBEAT_PROTOCOL_VERSION);
  assert.equal(heartbeat.backup_status, "not_configured");
  assert.equal(validateHeartbeat(heartbeat).valid, true);
});

test("rejects incomplete heartbeat payloads", () => {
  const result = validateHeartbeat({ protocol_version: HEARTBEAT_PROTOCOL_VERSION });
  assert.equal(result.valid, false);
  assert.ok(result.errors.includes("server_id is required"));
});
