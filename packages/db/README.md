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
