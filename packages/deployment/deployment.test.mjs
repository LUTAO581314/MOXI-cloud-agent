import test from "node:test";
import assert from "node:assert/strict";
import { buildCustomerDeploymentBundle, buildHermesEnv, buildServerAgentEnv } from "./index.mjs";

const options = {
  organizationId: "org_1",
  licenseId: "lic_1",
  serverId: "srv_1",
  platformBaseUrl: "https://platform.example.com/",
  licenseSecretRef: "secret-ref",
  serverAgentTokenRef: "agent-token-ref"
};

test("builds Hermes environment for customer server", () => {
  const env = buildHermesEnv(options);
  assert.match(env, /BAIRUI_PRODUCT_NAME=bairui Agent OS/);
  assert.match(env, /MOXI_SERVER_ID=srv_1/);
  assert.match(env, /MOXI_PLATFORM_BASE_URL=https:\/\/platform.example.com\//);
  assert.match(env, /BAIRUI_LICENSE_SECRET=secret-ref/);
  assert.doesNotMatch(env, /BEGIN (RSA|OPENSSH) PRIVATE KEY/);
});

test("builds server-agent outbound heartbeat environment", () => {
  const env = buildServerAgentEnv(options);
  assert.match(env, /BAIRUI_HERMES_HEARTBEAT_URL=http:\/\/127.0.0.1:8787\/platform\/heartbeat/);
  assert.match(env, /BAIRUI_PLATFORM_HEARTBEAT_URL=https:\/\/platform.example.com\/api\/server-heartbeat/);
  assert.match(env, /BAIRUI_SERVER_AGENT_TOKEN=agent-token-ref/);
});

test("builds complete customer deployment bundle", () => {
  const bundle = buildCustomerDeploymentBundle(options);
  assert.match(bundle.hermesEnv, /MOXI_LICENSE_FILE=\/etc\/bairui\/hermes-license.json/);
  assert.match(bundle.serverAgentEnv, /BAIRUI_PLATFORM_HEARTBEAT_URL=/);
  assert.match(bundle.instructions, /bairui Hermes Customer Deployment/);
  assert.match(bundle.instructions, /Platform `GET \/api\/servers`/);
});

test("requires deployment identity fields", () => {
  assert.throws(() => buildCustomerDeploymentBundle({}), /platformBaseUrl|serverId|organizationId|licenseId/);
});
