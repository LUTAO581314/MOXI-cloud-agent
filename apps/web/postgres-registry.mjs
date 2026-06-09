import { validateHeartbeat } from "../../packages/server-protocol/index.mjs";
import { buildHeartbeatUpsertSql, buildMigrationSql, heartbeatSqlParams } from "../../packages/db/schema.mjs";
import { summarizeServer } from "./server-registry.mjs";

export async function createPgPool(databaseUrl) {
  const { Pool } = await import("pg");
  return new Pool({ connectionString: databaseUrl });
}

export function createPostgresRegistryStorage(pool) {
  return {
    kind: "postgres",
    async migrate() {
      await pool.query(buildMigrationSql());
    },
    async recordHeartbeat(heartbeat, options = {}) {
      const validation = validateHeartbeat(heartbeat);
      if (!validation.valid) {
        return { accepted: false, status: 400, errors: validation.errors };
      }

      const receivedAt = options.receivedAt ?? new Date().toISOString();
      await pool.query(buildHeartbeatUpsertSql(), heartbeatSqlParams(heartbeat, receivedAt));
      return {
        accepted: true,
        status: 202,
        server: summarizeServer(heartbeat, receivedAt)
      };
    },
    async listServers() {
      const result = await pool.query(`
        select
          id as server_id,
          organization_id,
          license_id,
          license_status,
          hermes_version,
          health_status,
          database_status,
          backup_status,
          connector_status_summary,
          error_count_24h,
          brand_key,
          last_seen_at,
          last_heartbeat_at
        from customer_servers
        order by last_seen_at desc nulls last
      `);
      return result.rows;
    }
  };
}
