import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { writeCustomerDeliveryPackage } from "./delivery.mjs";
import { archiveDeliveryPackage } from "./archive.mjs";

test("archives delivery package as tar.gz with sha256", async () => {
  const dir = await mkdtemp(join(tmpdir(), "bairui-archive-"));
  try {
    const inputDir = join(dir, "delivery");
    const outputFile = join(dir, "delivery.tar.gz");
    await writeCustomerDeliveryPackage({
      organizationId: "org_1",
      licenseId: "lic_1",
      serverId: "srv_1",
      platformBaseUrl: "https://platform.example.com",
      licenseSecret: "secret",
      outputDir: inputDir,
      generatedAt: "2026-06-10T00:00:00.000Z"
    });

    const result = await archiveDeliveryPackage({ inputDir, outputFile });
    assert.equal(result.archive, outputFile);
    assert.equal(result.sha256.length, 64);
    assert.ok(result.files.includes("manifest.json"));
    assert.ok((await stat(outputFile)).size > 0);

    const bytes = await readFile(outputFile);
    assert.equal(bytes[0], 0x1f);
    assert.equal(bytes[1], 0x8b);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test("requires archive input and output", async () => {
  await assert.rejects(() => archiveDeliveryPackage({ inputDir: "", outputFile: "x.tar.gz" }), /inputDir is required/);
  await assert.rejects(() => archiveDeliveryPackage({ inputDir: "x", outputFile: "" }), /outputFile is required/);
});
