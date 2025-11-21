#!/bin/bash
# Fully automated deployment script
# Uses expect for password automation

VPS_IP="5.180.24.215"
VPS_USER="root"
VPS_PASS="U19TlpZ301V4"
VPS_PATH="/root/defectmaster-bot"

echo "=========================================="
echo "DefectMaster Bot - Automated Deployment"
echo "=========================================="
echo ""

# Check if expect is installed
if ! command -v expect &> /dev/null; then
    echo "Installing expect..."
    # This won't work on Git Bash, but will work on WSL or Linux
    echo "ERROR: expect not available in Git Bash"
    echo ""
    echo "Please use one of these methods:"
    echo ""
    echo "METHOD 1 - Manual (Recommended):"
    echo "  1. scp -r * root@5.180.24.215:/root/defectmaster-bot/"
    echo "  2. ssh root@5.180.24.215"
    echo "  3. bash /root/defectmaster-bot/server_setup.sh"
    echo ""
    echo "METHOD 2 - Use WSL:"
    echo "  Open WSL terminal and run this script from there"
    echo ""
    exit 1
fi

# Create expect script for scp
cat > /tmp/deploy_scp.exp << 'EOFEXP'
#!/usr/bin/expect -f
set timeout 300
set VPS_IP [lindex $argv 0]
set VPS_USER [lindex $argv 1]
set VPS_PASS [lindex $argv 2]
set VPS_PATH [lindex $argv 3]
set LOCAL_PATH [lindex $argv 4]

spawn scp -r $LOCAL_PATH/* ${VPS_USER}@${VPS_IP}:${VPS_PATH}/
expect {
    "yes/no" { send "yes\r"; exp_continue }
    "password:" { send "$VPS_PASS\r" }
}
expect eof
EOFEXP

chmod +x /tmp/deploy_scp.exp

# Create expect script for ssh
cat > /tmp/deploy_ssh.exp << 'EOFEXP'
#!/usr/bin/expect -f
set timeout 600
set VPS_IP [lindex $argv 0]
set VPS_USER [lindex $argv 1]
set VPS_PASS [lindex $argv 2]

spawn ssh ${VPS_USER}@${VPS_IP} "bash /root/defectmaster-bot/server_setup.sh"
expect {
    "yes/no" { send "yes\r"; exp_continue }
    "password:" { send "$VPS_PASS\r" }
}
expect eof
EOFEXP

chmod +x /tmp/deploy_ssh.exp

echo "[1/2] Uploading files to VPS..."
/tmp/deploy_scp.exp "$VPS_IP" "$VPS_USER" "$VPS_PASS" "$VPS_PATH" "$(pwd)"

echo ""
echo "[2/2] Running setup on VPS..."
/tmp/deploy_ssh.exp "$VPS_IP" "$VPS_USER" "$VPS_PASS"

# Cleanup
rm -f /tmp/deploy_scp.exp /tmp/deploy_ssh.exp

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Your bot is running at: @Stroy_Control_001_bot"
echo ""
