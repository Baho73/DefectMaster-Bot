#!/bin/bash
# Automatic deployment script for DefectMaster Bot
# VPS: 5.180.24.215

echo "=========================================="
echo "DefectMaster Bot - VPS Deployment"
echo "=========================================="
echo ""

# Update system
echo "[1/6] Updating system..."
apt update && apt upgrade -y

# Install Docker
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "[3/6] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    apt install docker-compose -y
else
    echo "Docker Compose already installed"
fi

# Create project directory
echo "[4/6] Creating project directory..."
mkdir -p /root/defectmaster-bot/data
cd /root/defectmaster-bot

# Check Docker versions
echo "[5/6] Checking installations..."
docker --version
docker-compose --version

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Upload project files to /root/defectmaster-bot/"
echo "2. Run: cd /root/defectmaster-bot && docker-compose up -d"
echo ""
