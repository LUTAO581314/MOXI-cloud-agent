# Bairui Platform Backend

百瑞云助理后端骨架，用于把静态前端升级为真实平台。

## Stack

- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Docker Compose

## Local Run

```powershell
docker compose up --build
```

Then open:

- API health: `http://127.0.0.1:8080/portal-api/health/`
- Admin: `http://127.0.0.1:8080/admin/`

## Development Commands

```powershell
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py test assistants
.\.venv\Scripts\python -m unittest bairui_agent.tests
.\.venv\Scripts\python manage.py seed_plans
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8081
```

Phase 1 API:

- `GET /portal-api/health/`
- `GET /portal-api/csrf/`
- `POST /portal-api/auth/register/`
- `POST /portal-api/auth/login/`
- `POST /portal-api/auth/email-code/request/`
- `POST /portal-api/auth/email-code/verify/`
- `POST /portal-api/auth/logout/`
- `GET /portal-api/auth/me/`
- `GET /portal-api/public/plans/`
- `GET|POST /portal-api/assistants/`
- `GET|POST /portal-api/provision-requests/`
- `POST /portal-api/provision-requests/:id/approve/` staff only
- `POST /portal-api/provision-requests/:id/reject/` staff only
- `GET /portal-api/assistants/:id/files/`
- `POST /portal-api/assistants/:id/upload_file/`
- `POST /portal-api/devices/pairing-code/`
- `POST /portal-api/agent/pair-device/`
- `WS /ws/agent/status/?device_id=<public_device_id>&token=<agent_token>`

## Local Agent CLI Prototype

Create a device pairing code from the web console/API, then pair this machine:

```powershell
.\.venv\Scripts\python -m bairui_agent.cli pair --api http://127.0.0.1:8081/portal-api/ --device-id <public_device_id> --code <pairing_code> --name "Owner Laptop"
```

Check local config without printing the token:

```powershell
.\.venv\Scripts\python -m bairui_agent.cli status
```

Send one WebSocket heartbeat:

```powershell
.\.venv\Scripts\python -m bairui_agent.cli run-once
```

Keep the local agent online:

```powershell
.\.venv\Scripts\python -m bairui_agent.cli run --interval 30
```

Authorize a local project directory for read-only indexing:

```powershell
.\.venv\Scripts\python -m bairui_agent.cli authorize "C:\path\to\project"
```

Print a safe file tree summary:

```powershell
.\.venv\Scripts\python -m bairui_agent.cli index
.\.venv\Scripts\python -m bairui_agent.cli index --json
```

The local indexer skips secrets and heavy folders by default, including `.env`, private keys, certificates, `node_modules`, `.git`, build outputs, virtual environments, and files above the configured size limit.

Storage model:

- Assistant activation creates `AssistantStorage`.
- Storage quota comes from `Subscription.plan.storage_limit_mb`.
- Assistant data is split into `workspace/`, `files/`, `memory/`, and `logs/`.
- File uploads are written under `files/`, then recorded as `AssistantFile`.
- Uploads fail when they exceed `AssistantStorage.quota_mb`.

## Environment

Copy `.env.example` to `.env` before production deployment.

## Deployment Notes

Recommended Caddy routing:

- `/portal-api/*` -> `127.0.0.1:8080`
- `/admin/*` -> `127.0.0.1:8080`
- `/ws/*` -> `127.0.0.1:8080`
- `/hermes/*` remains protected and proxied to the existing Hermes runtime.

## Product Design

- [Commercial platform blueprint](docs/COMMERCIAL_PLATFORM_BLUEPRINT.md)
- [Commercial implementation roadmap](docs/COMMERCIAL_IMPLEMENTATION_ROADMAP.md)
