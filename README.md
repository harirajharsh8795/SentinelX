# SentinelX: Autonomous Regulatory Intelligence & Compliance OS

> **One-Line Pitch:** An enterprise-grade, 100% offline agentic compliance operating system running on NVIDIA Jetson Orin Nano that ingests regulatory PDFs and translates them into actionable workflows via a self-correcting LangGraph multi-agent system.

---

## 🏛️ System Architecture

```
                                  +---------------------------------------+
                                  |          CYBERSECURITY PDF            |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |         PyPDF Text Extraction         |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |    Text Sanitization & Chunking       |
                                  |    (Input Sanitizer + Chunker)        |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |  Local Text Embedding Generation      |
                                  |  (SentenceTransformers / ChromaDB)    |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |        ChromaDB Vector Store          |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |     LangGraph Multi-Agent System      |
                                  |  +---------------------------------+  |
                                  |  |   Document Analyzer (SLM node)  |  |
                                  |  +---------------------------------+  |
                                  |                  |                    |
                                  |                  v                    |
                                  |  +---------------------------------+  |
                                  |  |   Compliance Checker (SLM node) |  |
                                  |  +---------------------------------+  |
                                  |                  |                    |
                                  |                  v                    |
                                  |  +---------------------------------+  |
                                  |  |   Cross-Regulation Node         |  |
                                  |  +---------------------------------+  |
                                  |                  |                    |
                                  |         (Grounding < 70%?)            |
                                  |         /                 \           |
                                  |     [Yes]                 [No]        |
                                  |       /                     \         |
                                  |      v                       v        |
                                  |  +---------------+   +-------------+  |
                                  |  |Self-Corrector |   |Task Gen     |  |
                                  |  |  (SLM Node)   |   | (SLM Node)  |  |
                                  |  +---------------+   +-------------+  |
                                  |        |                    |         |
                                  |        v                    v         |
                                  |  (Loop back)         (Persist & emit) |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |         FastAPI REST & WebSockets     |
                                  +---------------------------------------+
                                      /                               \
                                     v                                 v
                  +----------------------+                 +----------------------+
                  |   React Frontend     |                 |  Real-Time Telemetry |
                  | (Dashboard/Chat/KG)  |                 |     WebSocket Feeds  |
                  +----------------------+                 +----------------------+
```

---

## ⚡ EdgeMinds Track 3 Requirements Alignment

SentinelX is fully optimized for **EdgeMinds Track 3 (Agentic Task Automator)**:

*   **SLM as Brain [100% Offline]**: Orchestrated entirely via a local [Ollama](https://ollama.com) instance running `qwen2.5:1.5b`. No cloud API keys or external model dependencies are required for core analysis, guaranteeing strict data sovereignty.
*   **Custom Tools (8 Built-In Tools)**:
    1.  `RetrieverTool`: Semantic retrieval from ChromaDB vector index.
    2.  `MAPGeneratorTool`: Translates raw circular context into structured JSON Measurable Action Points (MAPs).
    3.  `DepartmentAssignmentTool`: Assigns corporate departments (e.g., Cybersecurity, Risk management) to actions.
    4.  `RiskScoringTool`: Automatically calculates risk and compliance percentages from detected exposures.
    5.  `ComplianceValidationTool`: Measures grounding scores and flags hallucinations by cross-checking sources.
    6.  `KnowledgeGraphTool`: Builds interactive relation maps between nodes (Circulars, Controls, Risks, Actions).
    7.  `WorkflowAutomationTool`: Automatically creates tasks inside the local SQLite database.
    8.  `AlertGeneratorTool`: Triggers real-time security alerts based on risk severities.
*   **Multi-Step LangGraph Orchestration**: Uses a compiled LangGraph `StateGraph` consisting of 5 distinct states:
    `document_analyzer` ➔ `compliance_checker` ➔ `cross_regulation` ➔ `self_corrector` ➔ `task_generator`.
*   **Self-Correction Loop**: Contains a conditional routing mechanism. If the `grounding_score` falls below `70%`, the state is routed to `self_corrector` which cleans and refines output context parameters and loops back up to 2 times to prevent hallucinated directives.

---

## 🚀 Key Features

*   **Real-time WebSocket Telemetry**: Every step (PDF parsed, vector embedding started, node executed, compliance score computed, tasks generated) broadcasts system logs immediately. Connected UI dashboards update in real-time.
*   **Offline Voice Compliance (faster-whisper)**: Built-in voice query transcription module utilizing `faster-whisper` (tiny model, CPU int8) to support voice commands on the edge.
*   **Interactive Impact Mapping**: D3-based interactive Knowledge Graph mapping circular regulations to operational departments and risk elements with direct double-click query transfer.
*   **Audit-Ready Trails**: Tracks every single node run with full intermediate state persistence in SQLite.

---

## 📂 Project Structure

```
CANARA SENTINEL AI/
├── backend/
│   ├── ai_agents/              # LangGraph multi-agent definitions and prompt templates
│   │   ├── agent_graph.py      # Compiled StateGraph, nodes, and conditional loops
│   │   ├── agent_tools.py      # Custom tools (Retriever, RiskScoring, Validation, etc.)
│   │   └── risk_agent.py       # Specific risk and compliance analysis loops
│   ├── api/                    # FastAPI route mapping and WebSockets
│   │   ├── auth.py             # User authentication and JWT endpoints
│   │   ├── routes.py           # REST endpoints (/telemetry, /dashboard, etc.)
│   │   └── stream.py           # WebSocket connections (AI streams, Alerts, Telemetry)
│   ├── database/               # Database setups and models
│   │   ├── database.py         # SQLite setup, WAL mode, session retry wrapper, write lock
│   │   └── models.py           # SQLAlchemy tables (Documents, Tasks, GraphState)
│   ├── rag/                    # Retrieval-Augmented Generation pipeline
│   │   ├── chunker.py          # Character-split and semantic paragraph chunking
│   │   ├── retriever.py        # Database connectors and hybrid retrieval filters
│   │   └── hybrid_search.py    # Hybrid TF-IDF / Dense vector search & reranking
│   ├── scrapers/               # Regulatory scraping scripts
│   ├── services/               # Core business logic handlers
│   │   ├── document_service.py # Ingestion, sanitization, and database persistence
│   │   ├── event_broadcaster.py# Telemetry WebSocket rooms and EventLogger definitions
│   │   └── chat_service.py     # Local SLM conversational memory wrapper
│   ├── utils/                  # Core helpers and security middleware
│   │   ├── input_sanitizer.py  # Prompt injection sanitization and context cleaning
│   │   ├── rate_limiter.py     # IP-based API rate limiting
│   │   └── config.py           # Startup environment validation and settings parser
│   ├── main.py                 # FastAPI application entrypoint
│   └── requirements.txt        # Python package dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/         # Layout modules (Sidebar, Notifications, TopBar)
│   │   ├── hooks/              # Custom React hooks (useFetch, useWebsocket)
│   │   ├── pages/              # Dashboard, Secure Ingestion, Tasks, KnowledgeGraph, Chat
│   │   ├── store/              # Zustand global client-side state store
│   │   ├── styles/             # Tailwind utility classes and animations
│   │   └── App.jsx             # Main routing shell
│   ├── tailwind.config.js      # Custom theme palettes and Jetson animation thresholds
│   └── vite.config.js          # Vite assets configuration
│
└── docs/                       # Hackathon presentations and talk tracks
    ├── DEMO_SCRIPT_HINGLISH.md # 5-minute judges talk track
    └── DEMO_FLOW.md            # Actionable slide flow script
```

---

## 🛠️ Quick Start

### A. Laptop Development (Simulation Mode)

1.  **Clone & Backend Setup**:
    ```bash
    cd backend
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/macOS:
    source .venv/bin/activate

    pip install -r requirements.txt
    cp .env.example .env
    ```
2.  **Run Backend Server**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
3.  **Frontend Setup**:
    ```bash
    cd ../frontend
    npm install
    npm run dev
    ```

---

### B. NVIDIA Jetson Orin Nano (8GB) - 100% Offline Production Setup

#### 1. Configure Swap Memory (Critical for 8GB Shared RAM)
Since Jetson Orin Nano shares its 8GB RAM between the CPU and Maxwell/Ampere GPU cores, a swap file is required to prevent Out-Of-Memory (OOM) process kills during parallel embedding generation and local SLM inference.

```bash
# Disable ZRAM if active (optional, depending on L4T version)
sudo systemctl disable nvzramconfig.service

# Create a 4GB Swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make the swap file mount permanent on reboot
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 2. Install & Launch Local Ollama
```bash
# Install Ollama on Linux Arm64
curl -fsSL https://ollama.com/install.sh | sh

# Pull the optimized SLM
ollama pull qwen2.5:1.5b
```

#### 3. Optimize Jetson Resources
Set the following environment variable configurations in `backend/.env` to configure memory boundaries on Jetson:
```env
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
JETSON_MODE=true
```
*(Setting `JETSON_MODE=true` disables heavy browser-side glassmorphism and spring transitions in the React UI, maintaining a constant 60 FPS in Chromium on the Jetson Orin Nano).*

#### 4. Run Post-Installation Patches (Critical for ChromaDB on Jetson/Windows)
ChromaDB contains internal SQLite and HNSW indexing bugs under custom edge configurations. Run the post-install patcher script inside your active virtual environment:
```bash
python post_install.py
```

#### 5. Run Startup Services
You can run the startup scripts located in the root folder to boot components automatically:
```bash
chmod +x ./start_sentinelx.sh ./health_check.sh
./start_sentinelx.sh
```

---

## 📺 Demo Video Placeholder

[![SentinelX EdgeMinds Demo Video](https://img.youtube.com/vi/placeholder/0.jpg)](https://www.youtube.com)

*(Click the image above to watch our 5-minute video presentation covering live LangGraph execution and WebSocket telemetry).*

---

## 👥 Team Info

*   **Lead AI Architect**: [Your Name] – LangGraph Orchestration & Backend Core
*   **Full-Stack Engineer**: [Partner Name] – React Dashboard & WebSocket Feeds
*   **Embedded & Systems Engineer**: [Partner Name] – Jetson Optimization & Swap Configurations