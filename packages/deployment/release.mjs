import { join } from "node:path";
import { archiveDeliveryPackage } from "./archive.mjs";
import { writeCustomerDeliveryPackage } from "./delivery.mjs";
import { verifyCustomerDeliveryPackage } from "./verify.mjs";

function requireString(options, key) {
  const value = options[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${key} is required`);
  }
  return value.trim();
}

function defaultOutputDir(options) {
  const organizationId = requireString(options, "organizationId");
  const serverId = requireString(options, "serverId");
  return join("tmp", "delivery", `${organizationId}-${serverId}`);
}

export async function releaseCustomerDeliveryPackage(options) {
  const outputDir = options.outputDir?.trim() || defaultOutputDir(options);
  const archiveFile = options.archiveFile?.trim() || `${outputDir}.tar.gz`;

  const writeResult = await writeCustomerDeliveryPackage({
    ...options,
    outputDir
  });
  const verification = await verifyCustomerDeliveryPackage({
    inputDir: outputDir,
    licenseSecret: options.licenseSecret
  });
  if (!verification.valid) {
    return {
      released: false,
      outputDir,
      archive: "",
      archiveSha256: "",
      errors: verification.errors,
      warnings: verification.warnings,
      writeResult,
      verification
    };
  }

  const archive = await archiveDeliveryPackage({
    inputDir: outputDir,
    outputFile: archiveFile
  });

  return {
    released: true,
    outputDir,
    archive: archive.archive,
    archiveSha256: archive.sha256,
    files: archive.files,
    warnings: verification.warnings,
    license_id: verification.license_id,
    organization_id: verification.organization_id,
    server_id: verification.server_id,
    manifest_version: verification.manifest_version
  };
}
