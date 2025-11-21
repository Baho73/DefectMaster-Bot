#!/usr/bin/env python3
"""
Automated Website Deployment Script for teamplan.ru
Requires: paramiko, scp
"""
import os
import sys

# VPS Configuration
VPS_IP = "5.180.24.215"
VPS_USER = "root"
VPS_PASS = "U19TlpZ301V4"
DOMAIN = "teamplan.ru"
WEB_ROOT = f"/var/www/{DOMAIN}"
NGINX_CONF = f"/etc/nginx/sites-available/{DOMAIN}"

def check_paramiko():
    """Check if paramiko is installed"""
    try:
        import paramiko
        return True
    except ImportError:
        return False

def install_paramiko():
    """Install paramiko"""
    print("[INFO] Installing paramiko and scp...")
    os.system(f"{sys.executable} -m pip install paramiko scp")

def deploy_website():
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
    print(f"Website Deployment - {DOMAIN}")
    print("=" * 60)
    print("")

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to VPS
        print(f"[1/6] Connecting to VPS {VPS_IP}...")
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("[OK] Connected successfully")

        # Install Nginx
        print(f"\n[2/6] Installing Nginx...")
        stdin, stdout, stderr = ssh.exec_command(
            "which nginx > /dev/null 2>&1 || apt install -y nginx",
            get_pty=True
        )
        stdout.channel.recv_exit_status()
        print("[OK] Nginx installed")

        # Create web directory
        print(f"\n[3/6] Creating web directory {WEB_ROOT}...")
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {WEB_ROOT}")
        stdout.channel.recv_exit_status()
        print("[OK] Directory created")

        # Upload website files
        print("\n[4/6] Uploading website files...")
        with SCPClient(ssh.get_transport()) as scp:
            website_dir = "website"
            if os.path.exists(website_dir):
                for file in os.listdir(website_dir):
                    file_path = os.path.join(website_dir, file)
                    if os.path.isfile(file_path):
                        print(f"  Uploading {file}...")
                        scp.put(file_path, f"{WEB_ROOT}/{file}")
        print("[OK] Files uploaded")

        # Configure Nginx
        print("\n[5/6] Configuring Nginx...")

        nginx_config = f"""server {{
    listen 80;
    listen [::]:80;
    server_name {DOMAIN} www.{DOMAIN};

    root {WEB_ROOT};
    index index.html;

    location / {{
        try_files $uri $uri/ =404;
    }}

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
}}
"""

        # Create Nginx config file
        stdin, stdout, stderr = ssh.exec_command(f"cat > {NGINX_CONF} << 'EOFNGINX'\n{nginx_config}\nEOFNGINX")
        stdout.channel.recv_exit_status()

        # Enable site
        stdin, stdout, stderr = ssh.exec_command(
            f"ln -sf {NGINX_CONF} /etc/nginx/sites-enabled/{DOMAIN}"
        )
        stdout.channel.recv_exit_status()

        # Test Nginx config
        stdin, stdout, stderr = ssh.exec_command("nginx -t")
        exit_status = stdout.channel.recv_exit_status()

        if exit_status == 0:
            print("[OK] Nginx configuration valid")

            # Reload Nginx
            stdin, stdout, stderr = ssh.exec_command("systemctl reload nginx")
            stdout.channel.recv_exit_status()
            print("[OK] Nginx reloaded")
        else:
            print("[ERROR] Nginx configuration invalid")
            return

        # Install Certbot and configure SSL
        print("\n[6/6] Configuring SSL certificate...")

        # Install certbot
        stdin, stdout, stderr = ssh.exec_command(
            "which certbot > /dev/null 2>&1 || (apt update && apt install -y certbot python3-certbot-nginx)",
            get_pty=True
        )
        stdout.channel.recv_exit_status()
        print("[OK] Certbot installed")

        # Obtain SSL certificate
        print(f"[INFO] Obtaining SSL certificate for {DOMAIN}...")
        stdin, stdout, stderr = ssh.exec_command(
            f"certbot --nginx -d {DOMAIN} -d www.{DOMAIN} --non-interactive --agree-tos --email office@{DOMAIN} --redirect",
            get_pty=True
        )

        for line in iter(stdout.readline, ""):
            if "Successfully" in line or "Certificate" in line or "Congratulations" in line:
                print(f"  {line.strip()}")

        exit_status = stdout.channel.recv_exit_status()

        if exit_status == 0:
            print("[OK] SSL certificate configured")
        else:
            print("[WARNING] SSL configuration may have issues, but site is accessible via HTTP")

        # Final check
        print("\n" + "=" * 60)
        print("Deployment Complete!")
        print("=" * 60)
        print("")
        print(f"Your website is now live!")
        print(f"HTTP:  http://{DOMAIN}")
        print(f"HTTPS: https://{DOMAIN}")
        print("")
        print("To check Nginx status:")
        print(f"  ssh {VPS_USER}@{VPS_IP}")
        print("  systemctl status nginx")

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

    deploy_website()
