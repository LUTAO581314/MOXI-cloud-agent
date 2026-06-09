export const HEARTBEAT_PROTOCOL_VERSION = "2026-06-10.p0";

const REQUIRED_STRING_FIELDS = [
  "server_id",
  "organization_id",
  "license_id",
  "license_status",
  "hermes_version",
  "health_status",
  "database_status",
  "backup_status",
  "brand_key",
  "created_at"
];

const VALID_LICENSE_STATUSES = new Set(["valid", "expired", "invalid", "unsigned", "missing_config"]);
const VALID_HEALTH_STATUSES = new Set(["ok", "partial", "degraded", "unavailable", "unknown"]);
const VALID_DATABASE_STATUSES = new Set(["ready", "missing_config", "missing_dependency", "unavailable", "failed"]);
const VALID_BACKUP_STATUSES = new Set(["not_configured", "ready", "running", "failed", "unknown"]);

function normalizeString(value, fallback = "") {
  if (value === undefined || value === null) {
    return fallback;
  }
  return String(value);
}

function normalizeNonNegativeInteger(value, fallback = 0) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0) {
    return fallback;
  }
  return Math.floor(number);
}

function normalizeConnectorSummary(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }
  const summary = {};
  for (const [key, rawStatus] of Object.entries(value)) {
    summary[String(key)] = normalizeString(rawStatus, "unknown");
  }
  return summary;
}

export function buildHeartbeat(input = {}) {
  return {
    protocol_version: HEARTBEAT_PROTOCOL_VERSION,
    server_id: normalizeString(input.server_id),
    organization_id: normalizeString(input.organization_id),
    license_id: normalizeString(input.license_id),
    license_status: normalizeString(input.license_status, "missing_config"),
    hermes_version: normalizeString(input.hermes_version),
    health_status: normalizeString(input.health_status, "unknown"),
    database_status: normalizeString(input.database_status, "missing_config"),
    backup_status: normalizeString(input.backup_status, "not_configured"),
    connector_status_summary: normalizeConnectorSummary(input.connector_status_summary),
    error_count_24h: normalizeNonNegativeInteger(input.error_count_24h),
    brand_key: normalizeString(input.brand_key, "bairui"),
    created_at: normalizeString(input.created_at, new Date().toISOString())
  };
}

export function validateHeartbeat(payload) {
  const errors = [];
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return { valid: false, errors: ["heartbeat payload must be an object"] };
  }

  for (const field of REQUIRED_STRING_FIELDS) {
    if (typeof payload[field] !== "string" || payload[field].trim() === "") {
      errors.push(`${field} is required`);
    }
  }

  if (payload.protocol_version !== HEARTBEAT_PROTOCOL_VERSION) {
    errors.push("protocol_version is unsupported");
  }
  if (!VALID_LICENSE_STATUSES.has(payload.license_status)) {
    errors.push("license_status is invalid");
  }
  if (!VALID_HEALTH_STATUSES.has(payload.health_status)) {
    errors.push("health_status is invalid");
  }
  if (!VALID_DATABASE_STATUSES.has(payload.database_status)) {
    errors.push("database_status is invalid");
  }
  if (!VALID_BACKUP_STATUSES.has(payload.backup_status)) {
    errors.push("backup_status is invalid");
  }
  if (!payload.connector_status_summary || typeof payload.connector_status_summary !== "object" || Array.isArray(payload.connector_status_summary)) {
    errors.push("connector_status_summary must be an object");
  }
  if (!Number.isInteger(payload.error_count_24h) || payload.error_count_24h < 0) {
    errors.push("error_count_24h must be a non-negative integer");
  }
  if (Number.isNaN(Date.parse(payload.created_at))) {
    errors.push("created_at must be an ISO timestamp");
  }

  return { valid: errors.length === 0, errors };
}
