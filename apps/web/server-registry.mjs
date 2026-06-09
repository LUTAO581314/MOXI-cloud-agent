import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { validateHeartbeat } from "../../packages/server-protocol/index.mjs";

const DEFAULT_REGISTRY_PATH = "./data/platform/server-registry.json";

export function loadRegistryConfig(env = process.env) {
  return {
    databaseUrl: env.BAIRUI_PLATFORM_DATABASE_URL ?? "",
    registryPath: env.BAIRUI_SERVER_REGISTRY_PATH ?? DEFAULT_REGISTRY_PATH,
    agentToken: env.BAIRUI_SERVER_AGENT_TOKEN ?? ""
  };
}

function emptyRegistry() {
  return {
    servers: {},
    heartbeats: []
  };
}

async function readRegistry(path) {
  try {
    return JSON.parse(await readFile(path, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") {
      return emptyRegistry();
    }
    throw error;
  }
}

async function writeRegistry(path, registry) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `${JSON.stringify(registry, null, 2)}\n`, "utf8");
}

export function summarizeServer(heartbeat, receivedAt) {
  return {
    server_id: heartbeat.server_id,
    organization_id: heartbeat.organization_id,
    license_id: heartbeat.license_id,
    license_status: heartbeat.license_status,
    hermes_version: heartbeat.hermes_version,
    health_status: heartbeat.health_status,
    database_status: heartbeat.database_status,
    backup_status: heartbeat.backup_status,
    connector_status_summary: heartbeat.connector_status_summary,
    error_count_24h: heartbeat.error_count_24h,
    brand_key: heartbeat.brand_key,
    last_seen_at: receivedAt,
    last_heartbeat_at: heartbeat.created_at
  };
}

export async function recordHeartbeat(heartbeat, options = {}) {
  const validation = validateHeartbeat(heartbeat);
  if (!validation.valid) {
    return { accepted: false, status: 400, errors: validation.errors };
  }

  const registryPath = options.registryPath ?? DEFAULT_REGISTRY_PATH;
  const receivedAt = options.receivedAt ?? new Date().toISOString();
  const registry = await readRegistry(registryPath);
  const summary = summarizeServer(heartbeat, receivedAt);

  registry.servers[heartbeat.server_id] = summary;
  registry.heartbeats.push({
    received_at: receivedAt,
    heartbeat
  });
  registry.heartbeats = registry.heartbeats.slice(-1000);

  await writeRegistry(registryPath, registry);
  return { accepted: true, status: 202, server: summary };
}

export async function listServers(options = {}) {
  const registryPath = options.registryPath ?? DEFAULT_REGISTRY_PATH;
  const registry = await readRegistry(registryPath);
  return Object.values(registry.servers).sort((left, right) => right.last_seen_at.localeCompare(left.last_seen_at));
}

export function isAuthorized(headers, config) {
  if (!config.agentToken) {
    return true;
  }
  return headers.authorization === `Bearer ${config.agentToken}`;
}

export function createJsonRegistryStorage(options = {}) {
  return {
    kind: "json",
    async recordHeartbeat(heartbeat, recordOptions = {}) {
      return recordHeartbeat(heartbeat, {
        registryPath: options.registryPath,
        ...recordOptions
      });
    },
    async listServers() {
      return listServers({ registryPath: options.registryPath });
    }
  };
}
