# MOXI Server Agent

The server agent is the customer-server management component for MOXI commercial
deployments.

It will run inside customer VPS or VM environments and report health summaries
back to MOXI Cloud Agent.

Responsibilities:

- register the server;
- report heartbeat;
- report resource summaries;
- report Hermes health;
- report backup status;
- collect diagnostic bundles after customer action;
- execute white-listed maintenance actions.

Forbidden in the first commercial version:

- arbitrary shell command execution;
- storing root passwords in the platform;
- uploading customer chat content;
- uploading Obsidian vault content;
- exposing an unauthenticated public control port.

Formal customer deployments should use VPS or VM isolation with Docker Compose
inside the customer environment.

## P0 Outbound Heartbeat

The first runnable agent cycle is implemented in `server-agent/index.mjs`.

It performs one safe outbound reporting cycle:

```text
Hermes GET /platform/heartbeat
  -> validate heartbeat with packages/server-protocol
  -> POST heartbeat to bairui platform
```

Environment variables:

- `BAIRUI_HERMES_HEARTBEAT_URL`: defaults to `http://127.0.0.1:8787/platform/heartbeat`.
- `BAIRUI_PLATFORM_HEARTBEAT_URL`: required platform receive endpoint.
- `BAIRUI_SERVER_AGENT_TOKEN`: optional bearer token issued by the platform.
- `BAIRUI_SERVER_AGENT_TIMEOUT_MS`: request timeout, default `10000`.

Run one report cycle:

```sh
npm run server-agent:once
```

Run the assisted deployment acceptance check:

```sh
npm run server-agent:acceptance
```

The acceptance command checks Hermes heartbeat, posts the heartbeat to the
platform, then confirms `GET /api/servers` contains the same server id. It
prints a JSON report and exits non-zero when any check fails.

The agent reports only operational metadata already exposed by Hermes heartbeat.
It does not upload prompts, chat history, files, Obsidian note bodies, memory
content, passwords, private keys, or model and connector secrets.
