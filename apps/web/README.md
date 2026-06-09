# MOXI Web Platform

This directory will contain the MOXI commercial web application:

- public website;
- customer console;
- admin console;
- deployment wizard;
- license management;
- server registry;
- support tickets;
- release and upgrade views.

Recommended stack:

- Next.js;
- TypeScript;
- Tailwind CSS;
- shadcn/ui;
- PostgreSQL;
- Prisma or Drizzle;
- Playwright.

This app must not contain Hermes runtime internals. It integrates with Hermes
through license files, server registration, release metadata, health summaries,
and support bundle workflows.

## P0 API

The first runnable platform API is implemented with Node standard library in
`apps/web/server.mjs`.

Endpoints:

- `GET /health`: platform API health check.
- `POST /api/server-heartbeat`: receive outbound heartbeat from server-agent.
- `GET /api/servers`: list the latest known server registry state.

Environment variables:

- `BAIRUI_PLATFORM_PORT`: local API port, default `8788`.
- `BAIRUI_SERVER_REGISTRY_PATH`: local JSON registry path, default
  `./data/platform/server-registry.json`.
- `BAIRUI_SERVER_AGENT_TOKEN`: optional bearer token required for heartbeat
  ingestion when set.

Run locally:

```sh
npm run platform:dev
```

This is a P0 local registry. PostgreSQL remains the commercial target for
production storage.
