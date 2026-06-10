import test from "node:test";
import assert from "node:assert/strict";
import { PLATFORM_SCHEMA_VERSION } from "./schema.mjs";
import { migratePlatformDatabase } from "./migrate.mjs";

test("requires database URL when pool is not injected", async () => {
  await assert.rejects(
    () => migratePlatformDatabase({ databaseUrl: "" }),
    /BAIRUI_PLATFORM_DATABASE_URL is required/
  );
});

test("runs migration SQL against injected pool", async () => {
  const calls = [];
  const result = await migratePlatformDatabase({
    pool: {
      async query(sql) {
        calls.push(sql);
      }
    }
  });

  assert.equal(result.status, "ready");
  assert.equal(result.schema_version, PLATFORM_SCHEMA_VERSION);
  assert.equal(calls.length, 1);
  assert.match(calls[0], /create table if not exists customer_servers/);
  assert.match(calls[0], /create table if not exists server_heartbeats/);
  assert.match(calls[0], /create table if not exists server_acceptance_reports/);
});

test("does not close injected pool", async () => {
  let closed = false;
  await migratePlatformDatabase({
    pool: {
      async query() {},
      async end() {
        closed = true;
      }
    }
  });

  assert.equal(closed, false);
});
