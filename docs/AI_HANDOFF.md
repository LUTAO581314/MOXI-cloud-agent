# AI Handoff

## Project Intent

MOXI Server Agent is planned as the infrastructure layer for MOXI-owned servers. The goal is to manage self-owned or customer-hosted servers safely through a centralized control plane.

Do not build a custom Linux distribution first. The preferred path is:

1. Standard Ubuntu / Debian / OpenCloudOS.
2. Install script.
3. cloud-init bootstrap.
4. Custom cloud image with Agent preinstalled.
5. MOXI control panel integration.

## Non-Negotiable Security Rules

- Never commit secrets, tokens, private keys, certificates, database passwords, or real server IPs.
- Agent should connect outbound to the control plane; do not expose an unauthenticated public control port.
- Do not implement arbitrary remote shell execution as a normal feature.
- Use whitelisted tasks with audit logs.
- Each server must have its own revocable credential.
- Proxy/admin users must not control host-level server actions.

## First Implementation Target

Build a minimal Agent that can:

- Register with the control plane using a one-time token.
- Send heartbeat and basic metrics.
- Report Docker Compose project status.
- Execute a small set of whitelisted actions.
- Return structured task results.

Suggested first whitelisted actions:

- `collect_metrics`
- `check_health`
- `restart_service`
- `reload_nginx`
- `deploy_project`

## Product Direction

This is for MOXI private deployment and future managed hosting service. Avoid positioning it as raw server rental at the start because that has higher abuse and compliance risk.

