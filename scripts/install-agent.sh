#!/usr/bin/env bash
set -euo pipefail

# MOXI Server Agent installer placeholder.
# This script intentionally contains no production secrets.

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "Please run as root."
  exit 1
fi

MOXI_AGENT_USER="${MOXI_AGENT_USER:-moxi-agent}"
MOXI_AGENT_DIR="${MOXI_AGENT_DIR:-/opt/moxi-agent}"

echo "Creating agent user and directories..."
id -u "$MOXI_AGENT_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$MOXI_AGENT_USER"
mkdir -p "$MOXI_AGENT_DIR" /var/log/moxi-agent /etc/moxi-agent
chown -R "$MOXI_AGENT_USER:$MOXI_AGENT_USER" "$MOXI_AGENT_DIR" /var/log/moxi-agent

echo "Installing base packages..."
if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  apt-get install -y ca-certificates curl gnupg nginx fail2ban ufw
else
  echo "Unsupported package manager. Install Docker, Nginx, Fail2ban, and firewall manually."
fi

cat >/etc/systemd/system/moxi-agent.service <<'SERVICE'
[Unit]
Description=MOXI Server Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=moxi-agent
Group=moxi-agent
WorkingDirectory=/opt/moxi-agent
EnvironmentFile=-/etc/moxi-agent/agent.env
ExecStart=/opt/moxi-agent/moxi-agent
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload

echo "Done. Put the agent binary at /opt/moxi-agent/moxi-agent and configure /etc/moxi-agent/agent.env."
