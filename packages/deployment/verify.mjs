import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { verifyLicensePayload } from "../license/index.mjs";
import { sha256Hex } from "./manifest.mjs";

const REQUIRED_FILES = ["hermes-license.json", "hermes.env", "server-agent.env", "instructions.md", "manifest.json"];
const REQUIRED_HERMES_ENV = [
  "BAIRUI_PRODUCT_NAME",
  "BAIRUI_BRAND_KEY",
  "HERMES_ENV",
  "HERMES_HOST",
  "HERMES_PORT",
  "MOXI_PLATFORM_BASE_URL",
  "MOXI_SERVER_ID",
  "MOXI_LICENSE_FILE",
  "BAIRUI_LICENSE_SECRET"
];
const REQUIRED_AGENT_ENV = [
  "BAIRUI_HERMES_HEARTBEAT_URL",
  "BAIRUI_PLATFORM_HEARTBEAT_URL",
  "BAIRUI_SERVER_AGENT_TOKEN"
];

function requireString(options, key) {
  const value = options[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${key} is required`);
  }
  return value.trim();
}

function parseEnv(content) {
  const values = {};
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }
    const index = trimmed.indexOf("=");
    if (index <= 0) {
      continue;
    }
    values[trimmed.slice(0, index)] = trimmed.slice(index + 1);
  }
  return values;
}

function isPlaceholder(value) {
  return /CHANGE_ME|SET_ON_CUSTOMER_SERVER|change-me/i.test(value);
}

function collectMissingEnv(values, keys) {
  return keys.filter((key) => !(key in values) || String(values[key]).trim() === "");
}

function collectPlaceholders(values) {
  return Object.entries(values)
    .filter(([, value]) => isPlaceholder(String(value)))
    .map(([key]) => key);
}

function validateUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export async function verifyCustomerDeliveryPackage(options) {
  const inputDir = requireString(options, "inputDir");
  const licenseSecret = requireString(options, "licenseSecret");
  const errors = [];
  const warnings = [];
  const files = {};

  for (const fileName of REQUIRED_FILES) {
    try {
      files[fileName] = await readFile(join(inputDir, fileName), "utf8");
    } catch {
      errors.push(`missing file: ${fileName}`);
    }
  }

  if (errors.length > 0) {
    return { valid: false, errors, warnings };
  }

  let license = {};
  let manifest = {};
  try {
    license = JSON.parse(files["hermes-license.json"]);
  } catch {
    errors.push("hermes-license.json is not valid JSON");
  }
  try {
    manifest = JSON.parse(files["manifest.json"]);
  } catch {
    errors.push("manifest.json is not valid JSON");
  }

  const licenseState = verifyLicensePayload(license, licenseSecret);
  if (licenseState.status !== "valid") {
    errors.push(`license is ${licenseState.status}: ${licenseState.error}`);
  }
  if (manifest.brand_key !== "bairui") {
    errors.push("manifest.json brand_key must be bairui");
  }
  if (manifest.license_id && license.license_id && manifest.license_id !== license.license_id) {
    errors.push("manifest.json license_id does not match license");
  }
  if (manifest.organization_id && license.organization_id && manifest.organization_id !== license.organization_id) {
    errors.push("manifest.json organization_id does not match license");
  }
  for (const [fileName, metadata] of Object.entries(manifest.files ?? {})) {
    if (fileName === "manifest.json") {
      continue;
    }
    if (!files[fileName]) {
      errors.push(`manifest references missing file: ${fileName}`);
      continue;
    }
    if (metadata.sha256 !== sha256Hex(files[fileName])) {
      errors.push(`manifest hash mismatch: ${fileName}`);
    }
  }

  const hermesEnv = parseEnv(files["hermes.env"]);
  const agentEnv = parseEnv(files["server-agent.env"]);
  for (const key of collectMissingEnv(hermesEnv, REQUIRED_HERMES_ENV)) {
    errors.push(`hermes.env missing ${key}`);
  }
  for (const key of collectMissingEnv(agentEnv, REQUIRED_AGENT_ENV)) {
    errors.push(`server-agent.env missing ${key}`);
  }

  if (hermesEnv.BAIRUI_BRAND_KEY !== "bairui") {
    errors.push("hermes.env BAIRUI_BRAND_KEY must be bairui");
  }
  if (license.license_id && hermesEnv.MOXI_SERVER_ID && !files["instructions.md"].includes(license.license_id)) {
    warnings.push("instructions.md does not mention license_id");
  }
  if (agentEnv.BAIRUI_PLATFORM_HEARTBEAT_URL && !validateUrl(agentEnv.BAIRUI_PLATFORM_HEARTBEAT_URL)) {
    errors.push("server-agent.env BAIRUI_PLATFORM_HEARTBEAT_URL must be http(s) URL");
  }
  if (agentEnv.BAIRUI_HERMES_HEARTBEAT_URL && !validateUrl(agentEnv.BAIRUI_HERMES_HEARTBEAT_URL)) {
    errors.push("server-agent.env BAIRUI_HERMES_HEARTBEAT_URL must be http(s) URL");
  }

  const placeholders = [
    ...collectPlaceholders(hermesEnv).map((key) => `hermes.env:${key}`),
    ...collectPlaceholders(agentEnv).map((key) => `server-agent.env:${key}`)
  ];
  for (const placeholder of placeholders) {
    warnings.push(`placeholder remains: ${placeholder}`);
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    license_id: license.license_id ?? "",
    organization_id: license.organization_id ?? "",
    server_id: hermesEnv.MOXI_SERVER_ID ?? "",
    manifest_version: manifest.manifest_version ?? ""
  };
}
