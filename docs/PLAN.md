# Canara Sentinel AI - Stepwise Build Plan

## Step 1: Project Skeleton + Tooling
- **Goal**: Clean `frontend/` + `backend/` structure, base configs, env template.
- **Why**: Team scaling + modularity + production feel.
- **Deliverables**:
  - Root: `.env.example`, `README.md`
  - Frontend: Vite + Tailwind setup
  - Backend: FastAPI entry + folders

## Step 2: Backend Core APIs (Scaffold)
- **Goal**: FastAPI app with required routes.
- **Why**: Frontend ko stable API contract mile.
- **Deliverables**:
  - `POST /upload-document`
  - `POST /analyze-document`
  - `GET /dashboard`
  - `GET /tasks`
  - `GET /alerts`
  - `GET /agent-logs`
  - `GET /audit-trail`

## Step 3: PDF Ingestion Pipeline ✅
- **Goal**: PDF parse, text extraction, chunking.
- **Why**: RBI circular ko AI-ready banana.
- **Deliverables**:
  - PyPDF parsing
  - Text cleaning + chunking
  - Upload storage

## Step 4: RAG Pipeline + Vector Store ✅
- **Goal**: Embeddings + ChromaDB indexing + retrieval.
- **Why**: Accurate semantic search and grounded answers.
- **Deliverables**:
  - Embeddings generator
  - ChromaDB client
  - Retriever for top-k context

## Step 5: Multi-Agent Orchestration ✅
- **Goal**: Compliance, Risk, Audit, Notification agents.
- **Why**: Specialized reasoning + explainability.
- **Deliverables**:
  - Agent modules
  - Orchestrator to aggregate outputs

## Step 6: AI Analysis Output (MAPs + Risk) ✅
- **Goal**: Summary, MAPs, risks, scores, reasoning.
- **Why**: Actionable compliance deliverables.
- **Deliverables**:
  - Compliance score
  - Risk score
  - MAP extraction
  - Explainable reasons

## Step 7: Logs + Audit Trail ✅
- **Goal**: Agent logs + audit timeline.
- **Why**: Banking traceability requirement.
- **Deliverables**:
  - Agent logs API
  - Audit trail API
  - Alert generation

## Step 8: Frontend Layout + Routing
- **Goal**: Sidebar, topbar, routing.
- **Why**: Enterprise UI baseline.
- **Deliverables**:
  - Dashboard layout
  - Page routes

## Step 9: Dashboard UI + Charts ✅
- **Goal**: Compliance score, trends, alerts, uploads.
- **Why**: Executive visibility.
- **Deliverables**:
  - Stat cards
  - Trend line chart
  - Risk donut chart

## Step 10: Upload + Analysis Pages ✅
- **Goal**: Upload flow + AI summary + MAPs + risks.
- **Why**: Core demo path.
- **Deliverables**:
  - Drag-drop UI
  - Analysis cards

## Step 11: Tasks + Logs + Audit Pages ✅
- **Goal**: Compliance tasks + agent logs + audit timeline.
- **Why**: Operations + traceability showcase.
- **Deliverables**:
  - Tables + lists
  - Timeline UI

## Step 12: API Integration (Frontend ↔ Backend) ✅
- **Goal**: Live data wiring with Axios.
- **Why**: End-to-end demo working.
- **Deliverables**:
  - API service
  - Hooks for fetch

## Step 13: Security + Env + Validation ✅
- **Goal**: Secure config + CORS + validation.
- **Why**: Production readiness.
- **Deliverables**:
  - Env handling
  - Basic validation

## Step 14: README + Demo Flow ✅
- **Goal**: Hackathon-ready documentation + demo script.
- **Why**: Judges + team presentation.
- **Deliverables**:
  - Setup steps
  - API docs
  - Demo flow

---

### Working Style
Har step ke baad:
- kya build hua
- kyun important hai
- kaise run hoga

Ab bol do kaunsa step se start karna hai. Recommended: **Step 2**.
