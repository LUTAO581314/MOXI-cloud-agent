import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { releaseCustomerDeliveryPackage } from "./release.mjs";

test("releases customer delivery package in one flow", async () => {
  const dir = await mkdtemp(join(tmpdir(), "bairui-release-"));
  try {
    const outputDir = join(dir, "delivery");
    const archiveFile = join(dir, "delivery.tar.gz");
    const result = await releaseCustomerDeliveryPackage({
      organizationId: "org_1",
      licenseId: "lic_1",
      serverId: "srv_1",
      platformBaseUrl: "https://platform.example.com",
      licenseSecret: "secret",
      outputDir,
      archiveFile,
      generatedAt: "2026-06-10T00:00:00.000Z"
    });

    assert.equal(result.released, true);
    assert.equal(result.license_id, "lic_1");
    assert.equal(result.server_id, "srv_1");
    assert.equal(result.archiveSha256.length, 64);
    assert.ok(result.files.includes("manifest.json"));
    assert.ok((await stat(archiveFile)).size > 0);
    assert.ok(result.warnings.some((warning) => warning.includes("placeholder remains")));
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test("requires release identity and license secret", async () => {
  await assert.rejects(
    () => releaseCustomerDeliveryPackage({ organizationId: "org_1", serverId: "srv_1" }),
    /licenseId is required|platformBaseUrl is required|licenseSecret is required/
  );
});
