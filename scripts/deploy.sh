#!/bin/bash

# ==============================================================================
#  MOCT (HFR) — VPS/VDS Deployment Script for Ubuntu / Debian
#  Automates Python env, CPU PyTorch installation, and Systemd service setup.
# ==============================================================================

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== starting MOCT Deployment ==="

# 1. Update system packages
echo "[1/6] Updating system packages..."
sudo apt update -y && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv sqlite3 git curl nginx

# 2. Setup directory
PROJECT_DIR="/var/www/CyrillicFontTransfer"
echo "[2/6] Preparing project folder at $PROJECT_DIR..."
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR

# 3. Create virtual environment
echo "[3/6] Setting up Python virtual environment..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
echo "[4/6] Installing dependencies..."
pip install --upgrade pip
# Install CPU version of PyTorch to save RAM/Disk and run fast on CPU
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
# Install remaining dependencies
pip install -r requirements.txt
# Ensure uvicorn and watchfiles are installed
pip install uvicorn gunicorn watchfiles

# 5. Setup Systemd Service
echo "[5/6] Generating Systemd service config..."
SERVICE_FILE="/etc/systemd/system/moct-backend.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=MOCT Cyrillic Font Matcher Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
Environment=PYTHONPATH=$PROJECT_DIR
Environment=ALLOWED_ORIGINS=*

[Install]
WantedBy=multi-user.target
EOL

echo "Reloading systemd, enabling and starting moct-backend service..."
sudo systemctl daemon-reload
sudo systemctl enable moct-backend
sudo systemctl restart moct-backend

# 6. Configure Nginx Reverse Proxy
echo "[6/6] Configuring Nginx reverse proxy..."
NGINX_CONF="/etc/nginx/sites-available/moct"

sudo bash -c "cat > $NGINX_CONF" <<EOL
server {
    listen 80;
    server_name _; # Replace with your domain name later

    # Max upload size for font images
    client_max_body_size 10M;

    # API Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Enable the site and restart Nginx
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default || true
sudo systemctl restart nginx

echo "=== MOCT Backend Deployment Complete ==="
echo "Status check:"
sudo systemctl status moct-backend --no-pager
