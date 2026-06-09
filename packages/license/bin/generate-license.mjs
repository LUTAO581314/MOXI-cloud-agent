#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { signLicense } from "../index.mjs";

function readArg(name, fallback = "") {
  const prefix = `--${name}=`;
  const value = process.argv.find((arg) => arg.startsWith(prefix));
  return value ? value.slice(prefix.length) : fallback;
}

const secret = process.env.BAIRUI_LICENSE_SECRET;
const licenseId = readArg("license-id", `lic_${Date.now()}`);
const organizationId = readArg("organization-id", "org_dev");
const plan = readArg("plan", "starter");
const expiresAt = readArg("expires-at", "");
const output = readArg("out", "");
const features = readArg("features", "jobs,chat,obsidian")
  .split(",")
  .map((item) => item.trim())
  .filter(Boolean);

const license = signLicense(
  {
    licenseId,
    organizationId,
    plan,
    features,
    expiresAt: expiresAt || undefined
  },
  secret
);

const body = `${JSON.stringify(license, null, 2)}\n`;
if (output) {
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, body, "utf8");
} else {
  process.stdout.write(body);
}
