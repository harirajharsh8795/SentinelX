#!/bin/bash

# ==============================================================================
# setup_jetson.sh
# One-time setup script for SentinelX on NVIDIA Jetson Orin Nano (8GB RAM)
# Hinglish Comments for easy configuration and troubleshooting during deployment.
# ==============================================================================

set -e # Kuchh bhi error aane par script abort ho jayegi.

echo "======================================================================"
echo "          SentinelX - NVIDIA Jetson Orin Nano Deployment Setup        "
echo "======================================================================"

CURRENT_DIR=$(pwd)
echo "[INFO] Current working directory: $CURRENT_DIR"

# 1. 4GB SWAP FILE CREATION
# Jetson Orin Nano has 8GB shared RAM (GPU + CPU). First load par RAM choke na ho,
# isiliye 4GB swap space add kar rahe hain (Ollama loading limits safety).
if [ ! -f /swapfile ]; then
    echo "[SWAP] Creating 4GB swap file (Jetson shared memory stabilization)..."
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "[SWAP] Swap file active!"
    free -h
else
    echo "[SWAP] Swapfile already exists. Skipping creation."
fi

# 2. SYSTEM DEPENDENCIES INSTALLATION
echo "[DEPS] Installing system dependencies (Python venv, curl, Nginx, Node.js)..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv curl nginx nodejs npm

# 3. OLLAMA & LOCAL SLM SETUP
# local offline mode setup. air-gapped demo ke liye model local cache mein store hoga.
if ! command -v ollama > /dev/null; then
    echo "[OLLAMA] Installing Ollama local inference engine..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "[OLLAMA] Ollama already installed."
fi

echo "[OLLAMA] Starting Ollama service and pulling qwen2.5:1.5b & embeddings models..."
sudo systemctl enable ollama
sudo systemctl restart ollama

# Wait for Ollama service to start responding
until curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "[OLLAMA] Waiting for Ollama engine to spin up..."
    sleep 2
done

# Pull local models
echo "[OLLAMA] Downloading qwen2.5:1.5b (reasoning/synthesis)..."
ollama pull qwen2.5:1.5b
echo "[OLLAMA] Downloading nomic-embed-text (local vector search)..."
ollama pull nomic-embed-text

# 4. BACKEND PYTHON VIRTUAL ENVIRONMENT SETUP
echo "[BACKEND] Creating python virtual environment and installing modules..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
echo "[BACKEND] Applying ChromaDB post-installation patches..."
python post_install.py
deactivate

# 5. FRONTEND COMPILATION & NGINX CONFIGURATION
echo "[FRONTEND] Ingesting node modules and building Vite production bundle..."
cd frontend
npm install
npm run build
cd "$CURRENT_DIR"

# Nginx config file compile kar rahe hain.
# location / -> serves built HTML/JS assets.
# location /api -> proxies websocket & standard requests to FastAPI port 8000.
echo "[NGINX] Writing custom server block config dynamically..."
NGINX_CONF="/etc/nginx/sites-available/sentinelx"

sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80 default_server;
    server_name _;

    root $CURRENT_DIR/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Activate Nginx configuration
sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
echo "[NGINX] Frontend configuration active and listening on HTTP port 80."

# 6. SYSTEMD SERVICE SETUP (BACKEND RUNTIME CONFIG)
# SentinelX FastAPI backend ko automatic daemon service configuration register kar rahe hain.
echo "[SYSTEMD] Registering sentinelx-backend.service daemon..."
SYSTEMD_SERVICE="/etc/systemd/system/sentinelx-backend.service"

sudo tee "$SYSTEMD_SERVICE" > /dev/null <<EOF
[Unit]
Description=SentinelX Autonomous Compliance System Backend
After=network.target ollama.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR/backend
ExecStart=$CURRENT_DIR/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
Environment=PATH=$CURRENT_DIR/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sentinelx-backend
sudo systemctl restart sentinelx-backend

echo "======================================================================"
echo "          SUCCESS: Setup complete! Run start_sentinelx.sh to start   "
echo "======================================================================"
