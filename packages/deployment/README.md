# Deployment Package

This package builds the first customer deployment bundle for bairui Hermes
servers managed by MOXI Cloud Agent.

It generates:

- Hermes environment file content.
- server-agent outbound heartbeat environment file content.
- customer/operator deployment instructions.
- signed license JSON when `delivery.mjs` is used.

The package does not generate or store real secrets. Production secrets must be
created by the platform secret service or operator workflow and injected as
server-side values.

Write a customer delivery package:

```sh
BAIRUI_LICENSE_SECRET=change-me npm run delivery:write -- \
  --organization-id=org_demo \
  --license-id=lic_demo \
  --server-id=srv_demo \
  --platform-url=https://platform.example.com \
  --out=./tmp/delivery/org_demo-srv_demo
```

Verify a customer delivery package before sending it:

```sh
BAIRUI_LICENSE_SECRET=change-me npm run delivery:verify -- \
  --in=./tmp/delivery/org_demo-srv_demo
```
