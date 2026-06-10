#!/usr/bin/env node
import { loadAcceptanceConfig, runAcceptance } from "../acceptance.mjs";

try {
  const report = await runAcceptance(loadAcceptanceConfig());
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  if (!report.accepted) {
    process.exitCode = 1;
  }
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
