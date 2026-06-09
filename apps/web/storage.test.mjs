import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createRegistryStorage } from "./storage.mjs";

test("creates JSON storage when database URL is missing", async () => {
  const dir = await mkdtemp(join(tmpdir(), "bairui-storage-"));
  try {
    const storage = await createRegistryStorage({
      databaseUrl: "",
      registryPath: join(dir, "server-registry.json")
    });
    assert.equal(storage.kind, "json");
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
