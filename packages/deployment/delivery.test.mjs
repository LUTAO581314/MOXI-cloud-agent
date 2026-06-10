import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { verifyLicensePayload } from "../license/index.mjs";
import { buildCustomerDeliveryPackage, writeCustomerDeliveryPackage } from "./delivery.mjs";

const options = {
  organizationId: "org_1",
  licenseId: "lic_1",
  serverId: "srv_1",
  platformBaseUrl: "https://platform.example.com",
  licenseSecret: "secret",
  serverAgentTokenRef: "token-ref",
  licenseSecretRef: "license-secret-ref"
};

test("builds signed customer delivery package", () => {
  const deliveryPackage = buildCustomerDeliveryPackage(options);
  assert.equal(verifyLicensePayload(deliveryPackage.license, "secret").status, "valid");
  assert.match(deliveryPackage.files["hermes.env"], /MOXI_SERVER_ID=srv_1/);
  assert.match(deliveryPackage.files["server-agent.env"], /BAIRUI_SERVER_AGENT_TOKEN=token-ref/);
  assert.match(deliveryPackage.files["instructions.md"], /bairui Hermes Customer Deployment/);
});

test("writes customer delivery package files", async () => {
  const outputDir = await mkdtemp(join(tmpdir(), "bairui-delivery-"));
  try {
    const result = await writeCustomerDeliveryPackage({ ...options, outputDir });
    assert.deepEqual(result.files.sort(), ["hermes-license.json", "hermes.env", "instructions.md", "server-agent.env"].sort());

    const license = JSON.parse(await readFile(join(outputDir, "hermes-license.json"), "utf8"));
    assert.equal(verifyLicensePayload(license, "secret").status, "valid");
    assert.match(await readFile(join(outputDir, "hermes.env"), "utf8"), /BAIRUI_LICENSE_SECRET=license-secret-ref/);
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
});

test("requires license secret and output directory", async () => {
  assert.throws(() => buildCustomerDeliveryPackage({ ...options, licenseSecret: "" }), /licenseSecret is required/);
  await assert.rejects(
    () => writeCustomerDeliveryPackage({ ...options, outputDir: "" }),
    /outputDir is required/
  );
});
