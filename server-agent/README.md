# MOXI Server Agent

The server agent is the customer-server management component for MOXI commercial
deployments.

It will run inside customer VPS or VM environments and report health summaries
back to MOXI Cloud Agent.

Responsibilities:

- register the server;
- report heartbeat;
- report resource summaries;
- report Hermes health;
- report backup status;
- collect diagnostic bundles after customer action;
- execute white-listed maintenance actions.

Forbidden in the first commercial version:

- arbitrary shell command execution;
- storing root passwords in the platform;
- uploading customer chat content;
- uploading Obsidian vault content;
- exposing an unauthenticated public control port.

Formal customer deployments should use VPS or VM isolation with Docker Compose
inside the customer environment.
