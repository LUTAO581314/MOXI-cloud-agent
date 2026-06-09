import { buildMigrationSql, PLATFORM_SCHEMA_VERSION } from "./schema.mjs";

export async function createPgPool(databaseUrl) {
  const { Pool } = await import("pg");
  return new Pool({ connectionString: databaseUrl });
}

export async function migratePlatformDatabase(options = {}) {
  const databaseUrl = options.databaseUrl ?? process.env.BAIRUI_PLATFORM_DATABASE_URL ?? "";
  if (!databaseUrl && !options.pool) {
    throw new Error("BAIRUI_PLATFORM_DATABASE_URL is required to run platform migrations.");
  }

  const pool = options.pool ?? await createPgPool(databaseUrl);
  const shouldClose = !options.pool;
  try {
    await pool.query(buildMigrationSql());
    return {
      status: "ready",
      schema_version: PLATFORM_SCHEMA_VERSION
    };
  } finally {
    if (shouldClose) {
      await pool.end();
    }
  }
}
