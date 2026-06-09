#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

ENV_FILE=${BAIRUI_PLATFORM_ENV_FILE:-/etc/bairui/platform.env}
INSTALL_SYSTEMD=${BAIRUI_INSTALL_SYSTEMD:-0}
RUN_MIGRATIONS=${BAIRUI_RUN_MIGRATIONS:-1}
SYSTEMD_UNIT_PATH=${BAIRUI_SYSTEMD_UNIT_PATH:-/etc/systemd/system/bairui-platform.service}

cd "$PROJECT_ROOT"

echo "bairui platform deploy: project root is $PROJECT_ROOT"

if ! command -v node >/dev/null 2>&1; then
  echo "node is required. Install Node.js before running this script." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required. Install npm before running this script." >&2
  exit 1
fi

if [ -f "$ENV_FILE" ]; then
  echo "loading environment from $ENV_FILE"
  set -a
  . "$ENV_FILE"
  set +a
else
  echo "environment file not found at $ENV_FILE"
  echo "copy infra/platform/env.example to $ENV_FILE and set real values before production use"
fi

if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

if [ "$RUN_MIGRATIONS" = "1" ]; then
  if [ -n "${BAIRUI_PLATFORM_DATABASE_URL:-}" ]; then
    npm run db:migrate
  else
    echo "skipping db:migrate because BAIRUI_PLATFORM_DATABASE_URL is empty"
  fi
fi

npm test

mkdir -p "$PROJECT_ROOT/tmp/platform"
cp "$PROJECT_ROOT/infra/platform/systemd/bairui-platform.service" "$PROJECT_ROOT/tmp/platform/bairui-platform.service"
echo "systemd unit template written to $PROJECT_ROOT/tmp/platform/bairui-platform.service"

if [ "$INSTALL_SYSTEMD" = "1" ]; then
  if [ "$(id -u)" -ne 0 ]; then
    echo "BAIRUI_INSTALL_SYSTEMD=1 requires root because it writes $SYSTEMD_UNIT_PATH" >&2
    exit 1
  fi
  cp "$PROJECT_ROOT/infra/platform/systemd/bairui-platform.service" "$SYSTEMD_UNIT_PATH"
  systemctl daemon-reload
  systemctl enable bairui-platform
  systemctl restart bairui-platform
  systemctl status bairui-platform --no-pager
else
  echo "systemd install skipped. Set BAIRUI_INSTALL_SYSTEMD=1 as root to install the service."
fi

echo "bairui platform deploy completed"
