#!/usr/bin/env node
import { writeCustomerDeliveryPackage } from "../delivery.mjs";

function readArg(name, fallback = "") {
  const prefix = `--${name}=`;
  const value = process.argv.find((arg) => arg.startsWith(prefix));
  return value ? value.slice(prefix.length) : fallback;
}

try {
  const result = await writeCustomerDeliveryPackage({
    organizationId: readArg("organization-id", "org_demo"),
    licenseId: readArg("license-id", `lic_${Date.now()}`),
    serverId: readArg("server-id", "srv_demo"),
    platformBaseUrl: readArg("platform-url", "https://platform.example.com"),
    outputDir: readArg("out", ""),
    licenseSecret: process.env.BAIRUI_LICENSE_SECRET ?? "",
    licenseSecretRef: readArg("license-secret-ref", "SET_ON_CUSTOMER_SERVER"),
    serverAgentTokenRef: readArg("server-agent-token-ref", "SET_ON_CUSTOMER_SERVER"),
    plan: readArg("plan", "starter"),
    features: readArg("features", "jobs,chat,obsidian"),
    expiresAt: readArg("expires-at", "")
  });
  process.stdout.write(`bairui delivery package written to ${result.outputDir}\n`);
  for (const fileName of result.files) {
    process.stdout.write(`- ${fileName}\n`);
  }
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
