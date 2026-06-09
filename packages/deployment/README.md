# Deployment Package

This package builds the first customer deployment bundle for bairui Hermes
servers managed by MOXI Cloud Agent.

It generates:

- Hermes environment file content.
- server-agent outbound heartbeat environment file content.
- customer/operator deployment instructions.

The package does not generate or store real secrets. Production secrets must be
created by the platform secret service or operator workflow and injected as
server-side values.
