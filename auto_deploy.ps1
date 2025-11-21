# Automatic VPS Deployment Script for DefectMaster Bot
# PowerShell version for Windows

$VPS_IP = "5.180.24.215"
$VPS_USER = "root"
$VPS_PASS = "U19TlpZ301V4"
$VPS_PATH = "/root/defectmaster-bot"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DefectMaster Bot - VPS Auto Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Upload files
Write-Host "[1/4] Uploading files to VPS..." -ForegroundColor Yellow

# Using scp (will prompt for password)
Write-Host "Password: $VPS_PASS" -ForegroundColor Green
Write-Host ""
Write-Host "Uploading project files..." -ForegroundColor Yellow

# Upload key files
$filesToUpload = @(
    ".env",
    "service-account.json",
    "docker-compose.yml",
    "Dockerfile",
    "main.py",
    "config.py",
    "requirements.txt"
)

foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        Write-Host "  Uploading $file..." -ForegroundColor Gray
        # Note: This will prompt for password interactively
        scp $file "${VPS_USER}@${VPS_IP}:${VPS_PATH}/"
    }
}

# Upload directories
$dirsToUpload = @("bot")

foreach ($dir in $dirsToUpload) {
    if (Test-Path $dir) {
        Write-Host "  Uploading $dir/..." -ForegroundColor Gray
        scp -r $dir "${VPS_USER}@${VPS_IP}:${VPS_PATH}/"
    }
}

Write-Host ""
Write-Host "[2/4] Installing Docker on VPS..." -ForegroundColor Yellow
Write-Host "This will be done via SSH (password required)" -ForegroundColor Green
Write-Host ""

Write-Host @"
========================================
NEXT STEPS (Manual SSH):
========================================

1. Connect to VPS:
   ssh root@5.180.24.215
   Password: U19TlpZ301V4

2. Run these commands:

   cd /root/defectmaster-bot

   # Install Docker
   apt update && apt upgrade -y
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   apt install docker-compose -y

   # Create data directory
   mkdir -p data

   # Start bot
   docker-compose up -d

   # Check logs
   docker-compose logs -f

========================================
"@ -ForegroundColor Cyan
