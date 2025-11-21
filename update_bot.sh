#!/bin/bash
# Quick update script for ai_service.py

SERVER="root@5.180.24.215"
REMOTE_DIR="/root/defectmaster-bot"

echo "Uploading updated ai_service.py..."
scp bot/services/ai_service.py $SERVER:$REMOTE_DIR/bot/services/ai_service.py

echo "Restarting bot..."
ssh $SERVER "cd $REMOTE_DIR && docker compose restart"

echo "Done! Check logs with: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs -f'"
