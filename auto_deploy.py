#!/usr/bin/env python3
"""
Automated VPS Deployment Script for DefectMaster Bot
Requires: paramiko (pip install paramiko)
"""
import os
import sys

# VPS Configuration
VPS_IP = "5.180.24.215"
VPS_USER = "root"
VPS_PASS = "U19TlpZ301V4"
VPS_PATH = "/root/defectmaster-bot"

def check_paramiko():
    """Check if paramiko is installed"""
    try:
        import paramiko
        return True
    except ImportError:
        return False

def install_paramiko():
    """Install paramiko"""
    print("[INFO] Installing paramiko...")
    os.system(f"{sys.executable} -m pip install paramiko scp")

def deploy():
    """Main deployment function"""
    try:
        import paramiko
        from scp import SCPClient
    except ImportError:
        print("[ERROR] paramiko/scp not installed")
        print("[INFO] Installing dependencies...")
        install_paramiko()
        import paramiko
        from scp import SCPClient

    print("=" * 60)
    print("DefectMaster Bot - Automated VPS Deployment")
    print("=" * 60)
    print("")

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to VPS
        print(f"[1/4] Connecting to VPS {VPS_IP}...")
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("[OK] Connected successfully")

        # Create directory
        print(f"\n[2/4] Creating directory {VPS_PATH}...")
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {VPS_PATH}/bot/handlers {VPS_PATH}/bot/services {VPS_PATH}/bot/database {VPS_PATH}/bot/utils {VPS_PATH}/data")
        stdout.channel.recv_exit_status()
        print("[OK] Directory created")

        # Upload files
        print("\n[3/4] Uploading files...")
        with SCPClient(ssh.get_transport()) as scp:
            files_to_upload = [
                ".env",
                "service-account.json",
                "docker-compose.yml",
                "Dockerfile",
                "main.py",
                "config.py",
                "requirements.txt",
                "server_setup.sh"
            ]

            for file in files_to_upload:
                if os.path.exists(file):
                    print(f"  Uploading {file}...")
                    scp.put(file, f"{VPS_PATH}/{file}")

            # Upload bot directory
            print("  Uploading bot/ directory...")
            for root, dirs, files in os.walk("bot"):
                for file in files:
                    if file.endswith('.py'):
                        local_path = os.path.join(root, file)
                        remote_path = f"{VPS_PATH}/{local_path}".replace("\\", "/")
                        print(f"    {local_path}")
                        scp.put(local_path, remote_path)

        print("[OK] Files uploaded")

        # Run setup script
        print("\n[4/4] Running setup on VPS...")
        print("This may take 3-5 minutes...")

        stdin, stdout, stderr = ssh.exec_command(
            f"cd {VPS_PATH} && chmod +x server_setup.sh && bash server_setup.sh",
            get_pty=True
        )

        # Print output in real-time
        for line in iter(stdout.readline, ""):
            print(line, end="")

        exit_status = stdout.channel.recv_exit_status()

        if exit_status == 0:
            print("\n" + "=" * 60)
            print("Deployment Complete!")
            print("=" * 60)
            print("")
            print("Your bot is now running!")
            print(f"Bot: @Stroy_Control_001_bot")
            print("")
            print("To check logs:")
            print(f"  ssh root@{VPS_IP}")
            print(f"  cd {VPS_PATH}")
            print("  docker-compose logs -f")
        else:
            print(f"\n[ERROR] Setup failed with exit code {exit_status}")

    except paramiko.AuthenticationException:
        print("[ERROR] Authentication failed. Check username/password.")
    except paramiko.SSHException as e:
        print(f"[ERROR] SSH error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    if not check_paramiko():
        print("[INFO] paramiko not found, installing...")
        install_paramiko()

    deploy()
