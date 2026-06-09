import crypto from "node:crypto";

export const SIGNATURE_FIELD = "signature";

export function canonicalPayload(payload) {
  const sorted = {};
  for (const key of Object.keys(payload).filter((key) => key !== SIGNATURE_FIELD).sort()) {
    const value = payload[key];
    if (value !== undefined) {
      sorted[key] = value;
    }
  }
  return JSON.stringify(sorted);
}

export function signLicensePayload(payload, secret) {
  if (!secret) {
    throw new Error("BAIRUI_LICENSE_SECRET is required to sign licenses.");
  }
  return crypto.createHmac("sha256", secret).update(canonicalPayload(payload), "utf8").digest("hex");
}

export function buildLicensePayload(options) {
  const now = new Date();
  const issuedAt = options.issuedAt ?? now.toISOString();
  const expiresAt = options.expiresAt ?? new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000).toISOString();
  return {
    license_id: options.licenseId,
    organization_id: options.organizationId,
    plan: options.plan ?? "starter",
    features: options.features ?? [],
    limits: options.limits ?? {},
    issued_at: issuedAt,
    expires_at: expiresAt,
    deployment_mode: options.deploymentMode ?? "customer_vm",
    product_name: options.productName ?? "bairui Agent OS",
    brand_key: "bairui",
    trademark_name: "bairui",
    logo_text: "bairui"
  };
}

export function signLicense(options, secret) {
  const payload = buildLicensePayload(options);
  return {
    ...payload,
    [SIGNATURE_FIELD]: signLicensePayload(payload, secret)
  };
}

export function verifyLicensePayload(payload, secret) {
  if (!payload || typeof payload !== "object") {
    return { status: "invalid", error: "license payload must be an object" };
  }
  if (!secret) {
    return { status: "unsigned", error: "BAIRUI_LICENSE_SECRET is not configured." };
  }
  if (!payload[SIGNATURE_FIELD]) {
    return { status: "invalid", error: "license signature is missing." };
  }
  const expected = signLicensePayload(payload, secret);
  const actual = String(payload[SIGNATURE_FIELD]);
  const expectedBytes = Buffer.from(expected, "utf8");
  const actualBytes = Buffer.from(actual, "utf8");
  if (expectedBytes.length !== actualBytes.length || !crypto.timingSafeEqual(expectedBytes, actualBytes)) {
    return { status: "invalid", error: "license signature is invalid." };
  }
  if (payload.expires_at && new Date(payload.expires_at).getTime() <= Date.now()) {
    return { status: "expired", error: "license is expired." };
  }
  return { status: "valid", error: "" };
}
