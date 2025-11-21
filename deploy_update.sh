#!/bin/bash
# Deploy updated files to VPS
# Usage: bash deploy_update.sh

SERVER="root@5.180.24.215"
REMOTE_DIR="/root/defectmaster-bot"

echo "=========================================="
echo "DefectMaster Bot - Deploying Updates"
echo "=========================================="
echo ""

echo "[1/4] Uploading bot code..."
scp -r bot ${SERVER}:${REMOTE_DIR}/

echo "[2/4] Uploading configuration files..."
scp .env config.py main.py requirements.txt docker-compose.yml Dockerfile service-account.json ${SERVER}:${REMOTE_DIR}/

echo "[3/4] Restarting bot on server..."
ssh $SERVER "cd $REMOTE_DIR && docker compose down && docker compose up -d --build"

echo "[4/4] Checking status..."
ssh $SERVER "cd $REMOTE_DIR && docker compose ps"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Check logs with: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs -f'"
