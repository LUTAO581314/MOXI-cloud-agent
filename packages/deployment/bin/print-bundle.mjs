#!/usr/bin/env node
import { buildCustomerDeploymentBundle } from "../index.mjs";

function readArg(name, fallback = "") {
  const prefix = `--${name}=`;
  const value = process.argv.find((arg) => arg.startsWith(prefix));
  return value ? value.slice(prefix.length) : fallback;
}

const bundle = buildCustomerDeploymentBundle({
  organizationId: readArg("organization-id", "org_demo"),
  licenseId: readArg("license-id", "lic_demo"),
  serverId: readArg("server-id", "srv_demo"),
  platformBaseUrl: readArg("platform-url", "https://platform.example.com"),
  licenseSecretRef: readArg("license-secret-ref", "CHANGE_ME_LICENSE_SECRET"),
  serverAgentTokenRef: readArg("server-agent-token-ref", "CHANGE_ME_SERVER_AGENT_TOKEN")
});

process.stdout.write("# hermes.env\n");
process.stdout.write(bundle.hermesEnv);
process.stdout.write("\n# server-agent.env\n");
process.stdout.write(bundle.serverAgentEnv);
process.stdout.write("\n# instructions.md\n");
process.stdout.write(bundle.instructions);
