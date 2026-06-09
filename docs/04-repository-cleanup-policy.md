# Repository Cleanup Policy

This repository is now the clean commercial platform and server-management home
for MOXI Agent OS.

## 1. Keep

Keep:

- `apps/web/` for the commercial platform;
- `packages/` for shared platform libraries;
- `server-agent/` for server-side agent code;
- `infra/` for deployment and operations templates;
- `docs/` for current commercial documentation;
- `LICENSE`;
- `.gitignore`;
- root `README.md`.

## 2. Remove

Remove:

- legacy branding;
- old assistant-hosting docs;
- copied prototype code that does not match current boundaries;
- real secrets;
- runtime data;
- generated logs;
- server IPs;
- private keys;
- TLS certificates;
- customer-specific `.env` files.

## 3. Boundary

Do not add Hermes runtime code to this repository.

Hermes belongs in `hermes-`. This repository integrates with Hermes through
licenses, server registration, deployment templates, health summaries, release
metadata, and support workflows.

Customer-facing brand, trademark, and logo fields must default to `bairui`.

## 4. Commercial Readiness Rule

A feature is not commercially ready until it has:

- UI or API entry;
- permission boundary;
- audit behavior;
- configuration path;
- error state;
- deployment path;
- test or verification command;
- documentation.
