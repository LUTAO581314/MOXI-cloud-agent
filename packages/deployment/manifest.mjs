import crypto from "node:crypto";

export const DELIVERY_MANIFEST_VERSION = "2026-06-10.p0";

export function sha256Hex(content) {
  return crypto.createHash("sha256").update(content, "utf8").digest("hex");
}

export function buildDeliveryManifest(options) {
  const files = {};
  for (const [fileName, content] of Object.entries(options.files ?? {})) {
    files[fileName] = {
      sha256: sha256Hex(content),
      bytes: Buffer.byteLength(content, "utf8")
    };
  }

  return {
    manifest_version: DELIVERY_MANIFEST_VERSION,
    generated_at: options.generatedAt ?? new Date().toISOString(),
    product: "bairui Agent OS",
    brand_key: "bairui",
    organization_id: options.organizationId,
    license_id: options.licenseId,
    server_id: options.serverId,
    platform_base_url: options.platformBaseUrl,
    files
  };
}
