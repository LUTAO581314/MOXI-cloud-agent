import test from "node:test";
import assert from "node:assert/strict";
import { buildDeliveryManifest, DELIVERY_MANIFEST_VERSION, sha256Hex } from "./manifest.mjs";

test("builds manifest with file hashes", () => {
  const manifest = buildDeliveryManifest({
    organizationId: "org_1",
    licenseId: "lic_1",
    serverId: "srv_1",
    platformBaseUrl: "https://platform.example.com",
    generatedAt: "2026-06-10T00:00:00.000Z",
    files: {
      "hermes.env": "MOXI_SERVER_ID=srv_1\n"
    }
  });

  assert.equal(manifest.manifest_version, DELIVERY_MANIFEST_VERSION);
  assert.equal(manifest.brand_key, "bairui");
  assert.equal(manifest.files["hermes.env"].sha256, sha256Hex("MOXI_SERVER_ID=srv_1\n"));
  assert.equal(manifest.files["hermes.env"].bytes, 21);
});
