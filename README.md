# MOXI Cloud Agent

MOXI Cloud Agent is the commercial website, customer platform, and server
management control plane for MOXI Agent OS.

This repository is not the Hermes runtime. Hermes remains the customer-side
Agent OS product kernel. This repository sells, delivers, licenses, monitors,
and supports Hermes deployments.

## Current Decision

The repository may be rebuilt from source according to the current commercial
plan. Existing Bairui prototype code under `bairui-platform/` is treated as
reference material, not as the final product boundary.

Keep or migrate only what helps the new platform:

- user registration and login;
- plan and subscription models;
- quotas;
- device/server pairing;
- WebSocket heartbeat;
- audit events;
- local agent prototype ideas;
- Docker Compose development pattern.

Replace or redesign:

- Bairui branding;
- assistant-hosting-first positioning;
- old docs that make Hermes only one optional runtime;
- route names that do not match MOXI commercial delivery;
- any demo-only flow that cannot become customer delivery.

## Product Role

`MOXI-cloud-agent` owns:

- official website;
- product pages;
- customer console;
- admin console;
- plans and subscriptions;
- license generation;
- deployment wizard;
- server registration;
- server heartbeat summaries;
- version and release management;
- support tickets;
- diagnostic bundle uploads;
- managed deployment operations.

`MOXI-cloud-agent` does not own:

- Hermes runtime internals;
- customer business chat content;
- customer Obsidian vault content;
- third-party model API keys;
- customer connector tokens;
- direct unrestricted shell control of servers.

## Three-Pillar Architecture

```text
Customer / Sales
  -> MOXI Website
  -> Customer Console
  -> License / Deployment Wizard
  -> VPS or VM
  -> Docker Compose
  -> Hermes Agent OS
  -> Health Summary Back To Platform
  -> Support / Renewal / Upgrade
```

## Repository Direction

Target structure:

```text
MOXI-cloud-agent/
  apps/
    web/                 # website, customer console, admin console
  packages/
    db/                  # platform database schema
    license/             # license generation and verification helpers
    server-protocol/     # server heartbeat and deployment protocol
    ui/                  # shared UI components
  server-agent/
    installer/
    agent/
    systemd/
  infra/
    docker/
    nginx/
    scripts/
  docs/
    00-platform-rebuild-plan.md
    01-server-management-plan.md
    02-license-and-deployment-flow.md
    03-hermes-platform-contract.md
  legacy/
    bairui-platform/     # optional migration target if we archive old code
```

The current `bairui-platform/` directory can either be migrated gradually or
archived before a clean rebuild.

## Recommended Technical Direction

Commercial platform:

- Next.js;
- TypeScript;
- PostgreSQL;
- Prisma or Drizzle;
- Tailwind CSS;
- shadcn/ui;
- Auth.js or equivalent auth layer;
- Docker Compose;
- GitHub Actions;
- Playwright.

Server management:

- VPS or VM per formal customer;
- Docker Compose inside each customer VM;
- outbound server heartbeat;
- no public unauthenticated control port;
- white-listed server actions only;
- diagnostic bundle upload only after customer action;
- no customer business data uploaded by default.

The existing Django prototype may still be useful if we decide speed is more
important than frontend velocity, but the recommended long-term customer
platform is a typed web platform with a strong UI and deployment wizard.

## Existing Prototype Inventory

Existing useful code:

- `bairui-platform/` Django + DRF backend;
- user/password and email-code login;
- plan, subscription, quota, storage, task, log, and memory models;
- device pairing API;
- WebSocket heartbeat endpoint;
- local CLI agent prototype;
- Docker Compose for Postgres, Redis, web, and worker.

Existing docs:

- [Server Agent Architecture](docs/architecture.md)
- [Security Boundary](docs/security.md)
- [Roadmap](docs/roadmap.md)
- [Commercial Platform Rebuild Plan](docs/00-platform-rebuild-plan.md)
- [Server Management Plan](docs/01-server-management-plan.md)

## Immediate Next Steps

1. Decide whether to archive `bairui-platform/` or migrate pieces from it.
2. Create the new platform skeleton.
3. Build license, customer organization, server registration, and deployment
   wizard first.
4. Keep Hermes as a separate deployable product.
5. Add server heartbeat contract between Hermes/customer VM and platform.
6. Prepare the first customer trial flow before adding full online payment.
