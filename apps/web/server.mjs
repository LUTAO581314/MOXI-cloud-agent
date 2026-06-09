import http from "node:http";
import { isAuthorized, listServers, loadRegistryConfig, recordHeartbeat } from "./server-registry.mjs";

function jsonResponse(response, status, payload) {
  const body = JSON.stringify(payload);
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body)
  });
  response.end(body);
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  if (chunks.length === 0) {
    return {};
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

export function createPlatformServer(config = loadRegistryConfig()) {
  return http.createServer(async (request, response) => {
    try {
      const url = new URL(request.url, "http://127.0.0.1");

      if (request.method === "GET" && url.pathname === "/health") {
        jsonResponse(response, 200, { status: "ok", service: "bairui-platform" });
        return;
      }

      if (request.method === "POST" && url.pathname === "/api/server-heartbeat") {
        if (!isAuthorized(request.headers, config)) {
          jsonResponse(response, 401, { error: "unauthorized" });
          return;
        }
        const payload = await readJson(request);
        const result = await recordHeartbeat(payload.heartbeat ?? payload, { registryPath: config.registryPath });
        jsonResponse(response, result.status, result.accepted ? { accepted: true, server: result.server } : { accepted: false, errors: result.errors });
        return;
      }

      if (request.method === "GET" && url.pathname === "/api/servers") {
        jsonResponse(response, 200, { servers: await listServers({ registryPath: config.registryPath }) });
        return;
      }

      jsonResponse(response, 404, { error: "not_found" });
    } catch (error) {
      jsonResponse(response, 500, { error: "internal_error", message: error.message });
    }
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const port = Number.parseInt(process.env.BAIRUI_PLATFORM_PORT ?? "8788", 10);
  const server = createPlatformServer();
  server.listen(port, "127.0.0.1", () => {
    console.log(`bairui platform API listening on http://127.0.0.1:${port}`);
  });
}
