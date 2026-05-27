#!/bin/bash
echo "=========================================="
echo "Starting SentinelX Backend Server..."
echo "=========================================="
cd backend && source .venv/Scripts/activate && uvicorn main:app --port 8000 &

# Wait a second for backend initialization
sleep 2

echo "=========================================="
echo "Starting SentinelX Frontend App..."
echo "=========================================="
cd ../frontend && npm run dev
