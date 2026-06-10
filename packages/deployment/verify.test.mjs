import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { writeCustomerDeliveryPackage } from "./delivery.mjs";
import { verifyCustomerDeliveryPackage } from "./verify.mjs";

const options = {
  organizationId: "org_1",
  licenseId: "lic_1",
  serverId: "srv_1",
  platformBaseUrl: "https://platform.example.com",
  licenseSecret: "secret"
};

async function withPackage(testFn) {
  const outputDir = await mkdtemp(join(tmpdir(), "bairui-verify-"));
  try {
    await writeCustomerDeliveryPackage({ ...options, outputDir });
    await testFn(outputDir);
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
}

test("verifies a generated delivery package", async () => {
  await withPackage(async (inputDir) => {
    const result = await verifyCustomerDeliveryPackage({
      inputDir,
      licenseSecret: "secret"
    });
    assert.equal(result.valid, true);
    assert.equal(result.license_id, "lic_1");
    assert.equal(result.server_id, "srv_1");
    assert.ok(result.warnings.some((warning) => warning.includes("placeholder remains")));
  });
});

test("rejects delivery package with wrong license secret", async () => {
  await withPackage(async (inputDir) => {
    const result = await verifyCustomerDeliveryPackage({
      inputDir,
      licenseSecret: "wrong"
    });
    assert.equal(result.valid, false);
    assert.ok(result.errors.some((error) => error.includes("license is invalid")));
  });
});

test("rejects delivery package with invalid heartbeat URL", async () => {
  await withPackage(async (inputDir) => {
    await writeFile(join(inputDir, "server-agent.env"), "BAIRUI_HERMES_HEARTBEAT_URL=not-a-url\nBAIRUI_PLATFORM_HEARTBEAT_URL=https://platform.example.com/api/server-heartbeat\nBAIRUI_SERVER_AGENT_TOKEN=token\n");
    const result = await verifyCustomerDeliveryPackage({
      inputDir,
      licenseSecret: "secret"
    });
    assert.equal(result.valid, false);
    assert.ok(result.errors.includes("server-agent.env BAIRUI_HERMES_HEARTBEAT_URL must be http(s) URL"));
    assert.ok(result.errors.includes("manifest hash mismatch: server-agent.env"));
  });
});

test("rejects delivery package with tampered manifest file hash", async () => {
  await withPackage(async (inputDir) => {
    await writeFile(join(inputDir, "hermes.env"), "BAIRUI_BRAND_KEY=bairui\n");
    const result = await verifyCustomerDeliveryPackage({
      inputDir,
      licenseSecret: "secret"
    });
    assert.equal(result.valid, false);
    assert.ok(result.errors.includes("manifest hash mismatch: hermes.env"));
  });
});

test("reports missing delivery files", async () => {
  const inputDir = await mkdtemp(join(tmpdir(), "bairui-missing-"));
  try {
    const result = await verifyCustomerDeliveryPackage({
      inputDir,
      licenseSecret: "secret"
    });
    assert.equal(result.valid, false);
    assert.ok(result.errors.includes("missing file: hermes-license.json"));
  } finally {
    await rm(inputDir, { recursive: true, force: true });
  }
});
