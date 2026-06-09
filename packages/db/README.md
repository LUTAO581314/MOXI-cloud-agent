# Platform Database Package

This package will own the commercial platform database schema and migration
helpers.

Initial domains:

- users;
- organizations;
- memberships;
- plans;
- subscriptions;
- orders;
- licenses;
- customer servers;
- server heartbeats;
- deployments;
- releases;
- support tickets;
- diagnostic uploads;
- audit logs.

The platform database must not store customer business chat content, Obsidian
vault text, model API keys, or connector tokens by default.

## P0 Schema

`schema.mjs` defines the first PostgreSQL schema for the commercial platform:

- `organizations`
- `licenses`
- `customer_servers`
- `server_heartbeats`

Print the migration SQL:

```sh
npm run db:migration:print
```

The first production path is:

```text
server-agent
  -> POST /api/server-heartbeat
  -> validate heartbeat
  -> upsert customer_servers
  -> append server_heartbeats
```

The current `apps/web` API still keeps a JSON registry for local P0 testing.
The SQL schema is the target for the next storage adapter.
