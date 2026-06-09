# Hermes Platform Contract

This document defines the boundary between Hermes and MOXI-cloud-agent.

## 1. Ownership

Hermes owns:

- Agent runtime;
- model gateway;
- tasks;
- approvals;
- tools;
- PostgreSQL production state;
- Obsidian writes;
- connectors;
- customer-side health.

MOXI-cloud-agent owns:

- website;
- customer console;
- admin console;
- license;
- plans;
- orders;
- deployment wizard;
- server registry;
- release metadata;
- support workflow.

## 2. Platform To Hermes

The platform may provide:

- license file;
- server_id;
- release metadata;
- deployment template;
- documentation links;
- support upload endpoint.

## 3. Hermes To Platform

Hermes may report:

- server_id;
- license_id;
- Hermes version;
- deployment mode;
- health status;
- backup status;
- connector summary;
- error count;
- last seen time.

## 4. Default Data Boundary

Hermes must not upload by default:

- chat content;
- Obsidian vault content;
- customer files;
- model API keys;
- connector tokens;
- database dumps;
- private logs with secrets.

Diagnostic bundles must be customer-triggered and must be redacted.
