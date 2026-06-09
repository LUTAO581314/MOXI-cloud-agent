# Server Protocol Package

This package will define the protocol between MOXI Cloud Agent, customer
servers, server-agent, and Hermes.

Protocol domains:

- server registration;
- heartbeat;
- health summary;
- backup status;
- release check;
- diagnostic bundle upload;
- white-listed server actions.

The protocol must default to outbound connections from the customer server to
the platform. It must not expose an unauthenticated public control port.

## P0 Heartbeat

`packages/server-protocol/index.mjs` defines the first commercial handoff
contract between bairui platform and customer servers.

Required fields:

- `protocol_version`
- `server_id`
- `organization_id`
- `license_id`
- `license_status`
- `hermes_version`
- `health_status`
- `database_status`
- `backup_status`
- `connector_status_summary`
- `error_count_24h`
- `brand_key`
- `created_at`

The heartbeat is operational metadata only. It must not contain user prompts,
conversation records, files, Obsidian note bodies, memory content, or secrets.
