#!/usr/bin/env node
import { verifyCustomerDeliveryPackage } from "../verify.mjs";

function readArg(name, fallback = "") {
  const prefix = `--${name}=`;
  const value = process.argv.find((arg) => arg.startsWith(prefix));
  return value ? value.slice(prefix.length) : fallback;
}

try {
  const result = await verifyCustomerDeliveryPackage({
    inputDir: readArg("in", ""),
    licenseSecret: process.env.BAIRUI_LICENSE_SECRET ?? ""
  });
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (!result.valid) {
    process.exitCode = 1;
  }
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
