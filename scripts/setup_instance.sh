#!/bin/bash
# setup_instance.sh - Script to setup an EC2 instance for the AI Agent
#
# Usage: sudo ./setup_instance.sh [instance-type]
#   instance-type: Optional, defaults to "production"
#
# This script:
# 1. Installs system dependencies
# 2. Creates the agent user and groups
# 3. Sets up the agent directory structure
# 4. Configures systemd service
# 5. Installs Python dependencies
# 6. Configures CloudWatch Agent

# (dale permiso con chmod +x)

#!/usr/bin/env bash

set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Ejecutar con sudo"; exit 1; }

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_USER=ai_agent_executor
WORKSPACE=/opt/agent_workspace
APP_DIR=/opt/agent

dnf install -y python3-pip amazon-cloudwatch-agent
pip3 install boto3

id "$AGENT_USER" &>/dev/null || useradd -m -s /bin/bash "$AGENT_USER"
mkdir -p "$WORKSPACE" "$APP_DIR"
chown "$AGENT_USER:$AGENT_USER" "$WORKSPACE"
chmod 700 "$WORKSPACE"

# Código propiedad de root: el agente puede leerlo pero no modificarlo
install -m 644 "$REPO_DIR/agent/agent.py" "$APP_DIR/agent.py"
install -m 644 "$REPO_DIR/systemd/ai-agent.service" /etc/systemd/system/ai-agent.service
systemctl daemon-reload

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c file:"$REPO_DIR/cloudwatch/amazon-cloudwatch-agent.json"

systemctl enable --now ai-agent
systemctl --no-pager status ai-agent || true