#!/bin/bash

# ==============================================================================
# health_check.sh
# Diagnostic check script for SentinelX on NVIDIA Jetson Orin Nano
# Hinglish Comments explaining metrics and troubleshooting.
# ==============================================================================

echo "======================================================================"
echo "          SentinelX System Health Diagnostics Overview                "
echo "======================================================================"

# 1. Check RAM and Swap usage
# Jetson's memory shared structure is checked here to see if swap is active and free.
echo -e "\n--- [MEM] RAM & Swap Utilization ---"
free -h

# 2. Check Ollama service and Model caches
echo -e "\n--- [OLLAMA] Service & Local Model Status ---"
if systemctl is-active --quiet ollama; then
    echo "Ollama Service: RUNNING"
    echo "Cached models in local library:"
    ollama list
else
    echo "Ollama Service: STOPPED ❌"
fi

# 3. Check FastAPI Backend Service
echo -e "\n--- [BACKEND] FastAPI Server Status ---"
if systemctl is-active --quiet sentinelx-backend; then
    echo "Backend systemd service: RUNNING"
else
    echo "Backend systemd service: STOPPED ❌"
fi

# Query backend health endpoint
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "FAILED")
if [ "$API_HEALTH" = "200" ]; then
    echo "Health API check: SUCCESS (HTTP 200) ✅"
    curl -s http://localhost:8000/health
    echo ""
else
    echo "Health API check: FAILED (HTTP Status: $API_HEALTH) ❌"
fi

# 4. Check Nginx Frontend Proxy
echo -e "\n--- [NGINX] Frontend Gateway Status ---"
if systemctl is-active --quiet nginx; then
    echo "Nginx Proxy Service: RUNNING"
    FRONTEND_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost || echo "FAILED")
    if [ "$FRONTEND_CHECK" = "200" ]; then
        echo "Web interface check: SUCCESS (HTTP 200) ✅"
    else
        echo "Web interface check: FAILED (HTTP Status: $FRONTEND_CHECK) ❌"
    fi
else
    echo "Nginx Proxy Service: STOPPED ❌"
fi

# 5. Check SQLite persistence access
echo -e "\n--- [SQLITE] Database Access & Schema Check ---"
if [ -f "./backend/sentinel_v2.db" ]; then
    echo "SQLite database file found at ./backend/sentinel_v2.db ✅"
    # Execute a small python script to check connection & tables
    python3 -c "
import sys
sys.path.append('backend')
from database.database import get_db_context
from database.models import Document
try:
    with get_db_context() as db:
        doc_count = db.query(Document).count()
        print(f'Database connection: SUCCESS! Active regulatory dossiers in catalog: {doc_count}')
except Exception as e:
    print(f'Database query: FAILED ❌ - {e}')
"
else
    echo "SQLite database file missing ❌ (Expected: ./backend/sentinel_v2.db)"
fi

# 6. Check ChromaDB collection status
# Vector DB initialize ho pa raha hai ya nahi aur metadata index verify karta hai.
echo -e "\n--- [CHROMADB] Vector Store Diagnostics ---"
python3 -c "
import sys
sys.path.append('backend')
try:
    from vector_db.chroma_client import get_client
    client = get_client()
    collections = client.list_collections()
    print('ChromaDB Vector Client initialization: SUCCESS ✅')
    print('Active Vector Collections list:')
    for col in collections:
        print(f' - Collection Name: {col.name} (Documents size: {col.count()})')
except Exception as e:
    print(f'ChromaDB Vector Client query: FAILED ❌ - {e}')
"

echo "======================================================================"
echo "          Diagnostics Complete! Check error markers (❌) if any.    "
echo "======================================================================"
