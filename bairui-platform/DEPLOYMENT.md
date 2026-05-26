# Bairui Platform Deployment Plan

## Server Facts

- Host: `38.76.190.53`
- Public domain: `bairui.chat`
- Static root: `/srv/bairui-chat/site`
- Current reverse proxy: Caddy
- Docker: available
- Docker Compose: available
- Existing Hermes dashboard: protected under `/hermes/`

## Target Layout

```text
/srv/bairui-chat/
  site/
  backend/
    docker-compose.yml
    .env
    app source
  private/
```

## Caddy Routing

Keep existing Hermes routes. Add user product backend routes:

```text
handle_path /portal-api/* {
  reverse_proxy 127.0.0.1:8080
}

handle /admin/* {
  reverse_proxy 127.0.0.1:8080
}

handle /ws/* {
  reverse_proxy 127.0.0.1:8080
}
```

Do not reuse `/api/*` for the product backend in phase 1 because the current Caddy config already protects and proxies `/api*` to Hermes.

## First Deploy Steps

1. Copy `bairui-platform` to `/srv/bairui-chat/backend`.
2. Create `/srv/bairui-chat/backend/.env` from `.env.example`.
3. Set strong `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`.
4. Run `docker compose up -d --build`.
5. Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

6. Confirm health:

```bash
curl http://127.0.0.1:8080/portal-api/health/
```

7. Add Caddy routes for `/portal-api/*`, `/admin/*`, and `/ws/*`.
8. Reload Caddy.

## Rollback

If backend deployment fails, remove only the new Caddy routes for `/portal-api/*`, `/admin/*`, and `/ws/*`. Static site and `/hermes/` should remain unaffected.
