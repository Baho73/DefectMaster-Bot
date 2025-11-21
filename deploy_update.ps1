# Deploy updated files to VPS
# Usage: .\deploy_update.ps1

$SERVER = "root@5.180.24.215"
$REMOTE_DIR = "/root/defectmaster-bot"
$LOCAL_DIR = "D:\Python\Stroykontrol_mvp_01"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DefectMaster Bot - Deploying Updates" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if scp is available
$scpAvailable = Get-Command scp -ErrorAction SilentlyContinue

if (-not $scpAvailable) {
    Write-Host "ERROR: scp not found. Please install OpenSSH Client or use Git Bash." -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Use WinSCP or run this script in Git Bash" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/4] Uploading bot code..." -ForegroundColor Green
scp -r "$LOCAL_DIR\bot" "${SERVER}:${REMOTE_DIR}/"

Write-Host "[2/4] Uploading configuration files..." -ForegroundColor Green
scp "$LOCAL_DIR\.env" "${SERVER}:${REMOTE_DIR}/.env"
scp "$LOCAL_DIR\config.py" "${SERVER}:${REMOTE_DIR}/config.py"
scp "$LOCAL_DIR\main.py" "${SERVER}:${REMOTE_DIR}/main.py"
scp "$LOCAL_DIR\requirements.txt" "${SERVER}:${REMOTE_DIR}/requirements.txt"
scp "$LOCAL_DIR\docker-compose.yml" "${SERVER}:${REMOTE_DIR}/docker-compose.yml"
scp "$LOCAL_DIR\Dockerfile" "${SERVER}:${REMOTE_DIR}/Dockerfile"
scp "$LOCAL_DIR\service-account.json" "${SERVER}:${REMOTE_DIR}/service-account.json"

Write-Host "[3/4] Restarting bot on server..." -ForegroundColor Green
ssh $SERVER "cd $REMOTE_DIR && docker compose down && docker compose up -d --build"

Write-Host "[4/4] Checking status..." -ForegroundColor Green
ssh $SERVER "cd $REMOTE_DIR && docker compose ps"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check logs with: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs -f'" -ForegroundColor Yellow
