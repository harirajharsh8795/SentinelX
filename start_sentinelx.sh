#!/bin/bash

# ==============================================================================
# start_sentinelx.sh
# Demo-day startup script for SentinelX on NVIDIA Jetson Orin Nano
# Hinglish Comments to guide manual inspection and runtime parameters.
# ==============================================================================

echo "======================================================================"
echo "          SentinelX - Starting Autonomous Intelligence Console        "
echo "======================================================================"

# 1. Start/Ensure Ollama service is active
echo "[OLLAMA] Checking Ollama daemon service..."
sudo systemctl start ollama

# Wait for Ollama port (11434) to start responding
until curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "[OLLAMA] Waiting for Ollama to spin up..."
    sleep 2
done
echo "[OLLAMA] Service active!"

# 2. Local LLM Warmup (Highly Critical on Jetson)
# Jetson Orin Nano pe pehli call weights load karne me 8-12s time leti hai.
# Agar hum warmup run na karein to front-end request timeout/slow performance face karega.
# Hum ek fake request forward karke weights warm up/pre-load kar rahe hain.
echo "[OLLAMA] Warming up local model qwen2.5:1.5b (Loading weights to GPU memory)..."
curl -s -X POST http://localhost:11434/api/chat -d '{
  "model": "qwen2.5:1.5b",
  "messages": [{"role": "user", "content": "ping"}],
  "stream": false
}' > /dev/null
echo "[OLLAMA] Warmup complete! Model loaded into unified RAM."

# 3. Ensure FastAPI Backend daemon is running
echo "[BACKEND] Restarting SentinelX FastAPI systemd backend service..."
sudo systemctl restart sentinelx-backend

# Wait for Backend port (8000) to respond
until curl -s http://localhost:8000/health > /dev/null; do
    echo "[BACKEND] Waiting for FastAPI server on http://localhost:8000..."
    sleep 2
done
echo "[BACKEND] FastAPI Backend is live!"

# 4. Trigger Health Check report
if [ -f ./health_check.sh ]; then
    bash ./health_check.sh
else
    echo "[WARN] health_check.sh file not found. Skipping quick health report."
fi

# 5. Open Chrome/Default Browser (Desktop GUI check)
# Agar Jetson headless console mode par nahi hai aur GUI screen connected hai,
# to ye browser directly localhost portal (nginx default) trigger karega.
echo "[BROWSER] Launching client panel..."
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost"
elif command -v google-chrome > /dev/null; then
    google-chrome --no-sandbox "http://localhost" &
elif command -v firefox > /dev/null; then
    firefox "http://localhost" &
else
    echo "[INFO] GUI browser command not found. You can open SentinelX at http://localhost on any device on the network."
fi

echo "======================================================================"
echo "          SentinelX is operational! Press Ctrl+C to exit logs        "
echo "======================================================================"

# Stream logs in console to observe system actions in real-time
sudo journalctl -u sentinelx-backend -f -n 50
