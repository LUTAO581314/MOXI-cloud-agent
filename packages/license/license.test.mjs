import test from "node:test";
import assert from "node:assert/strict";
import { signLicense, verifyLicensePayload } from "./index.mjs";

test("signs and verifies a bairui license", () => {
  const license = signLicense(
    {
      licenseId: "lic_1",
      organizationId: "org_1",
      plan: "starter",
      features: ["jobs", "chat"],
      expiresAt: "2999-01-01T00:00:00.000Z"
    },
    "secret"
  );
  assert.equal(license.brand_key, "bairui");
  assert.equal(verifyLicensePayload(license, "secret").status, "valid");
});

test("detects invalid signatures", () => {
  const license = signLicense({ licenseId: "lic_1", organizationId: "org_1" }, "secret");
  license.plan = "business";
  assert.equal(verifyLicensePayload(license, "secret").status, "invalid");
});
