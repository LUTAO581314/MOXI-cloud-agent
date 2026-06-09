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
