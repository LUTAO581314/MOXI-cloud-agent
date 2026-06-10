#!/usr/bin/env node
import { archiveDeliveryPackage } from "../archive.mjs";

function readArg(name, fallback = "") {
  const prefix = `--${name}=`;
  const value = process.argv.find((arg) => arg.startsWith(prefix));
  return value ? value.slice(prefix.length) : fallback;
}

try {
  const result = await archiveDeliveryPackage({
    inputDir: readArg("in", ""),
    outputFile: readArg("out", "")
  });
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
