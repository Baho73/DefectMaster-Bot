#!/bin/bash
# Full server setup script
# Run this on VPS after uploading files

echo "=========================================="
echo "DefectMaster Bot - Server Setup"
echo "=========================================="
echo ""

# Update system
echo "[1/5] Updating system..."
apt update -y
apt upgrade -y

# Install Docker
echo "[2/5] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm -f get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "[3/5] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    apt install docker-compose -y
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose already installed"
fi

# Setup project
echo "[4/5] Setting up project..."
cd /root/defectmaster-bot
mkdir -p data

# Check required files
echo "Checking required files..."
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    exit 1
fi

if [ ! -f "service-account.json" ]; then
    echo "ERROR: service-account.json not found!"
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    echo "ERROR: docker-compose.yml not found!"
    exit 1
fi

echo "All required files present"

# Start bot
echo "[5/5] Starting bot..."
docker-compose up -d

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Bot is starting..."
echo ""
echo "Check logs with:"
echo "  docker-compose logs -f"
echo ""
echo "Check status with:"
echo "  docker-compose ps"
echo ""
