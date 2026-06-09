import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("platform deployment assets avoid real secrets and expose required commands", async () => {
  const envExample = await readFile("infra/platform/env.example", "utf8");
  const deployScript = await readFile("infra/platform/scripts/deploy-platform.sh", "utf8");
  const service = await readFile("infra/platform/systemd/bairui-platform.service", "utf8");

  assert.match(envExample, /BAIRUI_PLATFORM_DATABASE_URL=/);
  assert.match(envExample, /change-me/);
  assert.match(deployScript, /npm ci|npm install/);
  assert.match(deployScript, /npm run db:migrate/);
  assert.match(deployScript, /npm test/);
  assert.match(service, /ExecStart=\/usr\/bin\/npm run platform:dev/);
  assert.doesNotMatch(`${envExample}\n${deployScript}\n${service}`, /BEGIN (RSA|OPENSSH) PRIVATE KEY/);
});
