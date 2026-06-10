import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { signLicense } from "../license/index.mjs";
import { buildCustomerDeploymentBundle } from "./index.mjs";
import { buildDeliveryManifest } from "./manifest.mjs";

function requireString(options, key) {
  const value = options[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${key} is required`);
  }
  return value.trim();
}

function splitFeatures(value) {
  if (Array.isArray(value)) {
    return value.map(String).map((item) => item.trim()).filter(Boolean);
  }
  if (typeof value !== "string") {
    return [];
  }
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

export function buildCustomerDeliveryPackage(options) {
  const licenseSecret = requireString(options, "licenseSecret");
  const organizationId = requireString(options, "organizationId");
  const licenseId = requireString(options, "licenseId");
  const serverId = requireString(options, "serverId");
  const platformBaseUrl = requireString(options, "platformBaseUrl");

  const license = signLicense(
    {
      licenseId,
      organizationId,
      plan: options.plan ?? "starter",
      features: splitFeatures(options.features ?? "jobs,chat,obsidian"),
      expiresAt: options.expiresAt || undefined,
      deploymentMode: options.deploymentMode ?? "customer_vm"
    },
    licenseSecret
  );

  const bundle = buildCustomerDeploymentBundle({
    ...options,
    organizationId,
    licenseId,
    serverId,
    platformBaseUrl,
    licenseSecretRef: options.licenseSecretRef ?? "SET_ON_CUSTOMER_SERVER",
    serverAgentTokenRef: options.serverAgentTokenRef ?? "SET_ON_CUSTOMER_SERVER"
  });

  const files = {
    "hermes-license.json": `${JSON.stringify(license, null, 2)}\n`,
    "hermes.env": bundle.hermesEnv,
    "server-agent.env": bundle.serverAgentEnv,
    "instructions.md": bundle.instructions
  };
  const manifest = buildDeliveryManifest({
    organizationId,
    licenseId,
    serverId,
    platformBaseUrl,
    generatedAt: options.generatedAt,
    files
  });
  files["manifest.json"] = `${JSON.stringify(manifest, null, 2)}\n`;

  return { license, manifest, files };
}

export async function writeCustomerDeliveryPackage(options) {
  const outputDir = requireString(options, "outputDir");
  const deliveryPackage = buildCustomerDeliveryPackage(options);
  await mkdir(outputDir, { recursive: true });
  for (const [fileName, content] of Object.entries(deliveryPackage.files)) {
    await writeFile(join(outputDir, fileName), content, "utf8");
  }
  return {
    outputDir,
    files: Object.keys(deliveryPackage.files),
    license_id: deliveryPackage.license.license_id,
    organization_id: deliveryPackage.license.organization_id,
    manifest_version: deliveryPackage.manifest.manifest_version
  };
}
