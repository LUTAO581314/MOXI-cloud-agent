import { validateHeartbeat } from "../packages/server-protocol/index.mjs";

export function loadAgentConfig(env = process.env) {
  return {
    hermesHeartbeatUrl: env.BAIRUI_HERMES_HEARTBEAT_URL ?? "http://127.0.0.1:8787/platform/heartbeat",
    platformHeartbeatUrl: env.BAIRUI_PLATFORM_HEARTBEAT_URL ?? "",
    agentToken: env.BAIRUI_SERVER_AGENT_TOKEN ?? "",
    timeoutMs: Number.parseInt(env.BAIRUI_SERVER_AGENT_TIMEOUT_MS ?? "10000", 10)
  };
}

function withTimeout(timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return { controller, clear: () => clearTimeout(timer) };
}

export async function fetchHermesHeartbeat(config, fetchImpl = fetch) {
  const timeout = withTimeout(config.timeoutMs);
  try {
    const response = await fetchImpl(config.hermesHeartbeatUrl, {
      method: "GET",
      signal: timeout.controller.signal,
      headers: { accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Hermes heartbeat request failed with HTTP ${response.status}`);
    }
    const body = await response.json();
    const heartbeat = body.heartbeat ?? body;
    const validation = validateHeartbeat(heartbeat);
    if (!validation.valid) {
      throw new Error(`Hermes heartbeat is invalid: ${validation.errors.join("; ")}`);
    }
    return heartbeat;
  } finally {
    timeout.clear();
  }
}

export async function postHeartbeat(config, heartbeat, fetchImpl = fetch) {
  if (!config.platformHeartbeatUrl) {
    throw new Error("BAIRUI_PLATFORM_HEARTBEAT_URL is required to report heartbeat.");
  }

  const headers = {
    accept: "application/json",
    "content-type": "application/json"
  };
  if (config.agentToken) {
    headers.authorization = `Bearer ${config.agentToken}`;
  }

  const timeout = withTimeout(config.timeoutMs);
  try {
    const response = await fetchImpl(config.platformHeartbeatUrl, {
      method: "POST",
      signal: timeout.controller.signal,
      headers,
      body: JSON.stringify({ heartbeat })
    });
    if (!response.ok) {
      throw new Error(`Platform heartbeat report failed with HTTP ${response.status}`);
    }
    return response.json();
  } finally {
    timeout.clear();
  }
}

export async function runOnce(config = loadAgentConfig(), fetchImpl = fetch) {
  const heartbeat = await fetchHermesHeartbeat(config, fetchImpl);
  const result = await postHeartbeat(config, heartbeat, fetchImpl);
  return { heartbeat, result };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runOnce()
    .then(({ heartbeat }) => {
      console.log(`bairui server-agent reported heartbeat for ${heartbeat.server_id}`);
    })
    .catch((error) => {
      console.error(error.message);
      process.exitCode = 1;
    });
}
