# Canara Sentinel AI - Hackathon Demo Flow

## 1. Opening (15-20 sec)
"We built Canara Sentinel AI, an agentic regulatory intelligence platform that reads RBI circulars and converts them into actionable compliance tasks with full audit traceability."

## 2. Problem Context (20 sec)
- Banks receive frequent RBI updates, manual interpretation causes delays.
- Compliance teams need fast, explainable action items and risk signals.

## 3. Upload → AI Processing (30 sec)
- Show Upload page.
- Upload an RBI circular PDF.
- Highlight live processing steps:
  - Parsing PDF → Chunking → RAG retrieval → Agents run
- Mention multi-agent orchestration.

## 4. Analysis Results (45 sec)
- Navigate to Analysis page.
- Show:
  - AI Summary
  - Extracted MAPs (department + deadline + severity)
  - Risk Analysis + source sections
  - Executive Insights
  - Why AI flagged this (reasoning)

## 5. Compliance Operations View (30 sec)
- Go to Tasks page:
  - Show priority, deadlines
- Agent Logs page:
  - Show traceable AI actions
- Audit Timeline:
  - Show compliance history

## 6. Executive Dashboard (30 sec)
- Open Dashboard:
  - Compliance score
  - Risk alerts banner
  - Severity breakdown
  - Future risk prediction

## 7. Close (15 sec)
"This converts regulatory PDFs into measurable action plans with real-time AI intelligence and audit-grade transparency."

---

# Presentation Script (Short)

## Slide 1: Vision
"Canara Sentinel AI delivers agentic compliance intelligence at RBI scale."

## Slide 2: Architecture
"PDF ingestion → RAG → multi-agent Gemini → structured tasks and risk scores."

## Slide 3: Live Demo
"Upload → AI summary → MAPs → Risks → Audit trail."

## Slide 4: Impact
"Faster compliance response, lower risk exposure, stronger audit readiness."

---

# Judge Explanation (1 minute)
- **Innovation**: Multi-agent AI with explainability for RBI circulars.
- **Practicality**: Direct MAP extraction with departments + deadlines.
- **Scalability**: ChromaDB + FastAPI architecture ready for enterprise.
- **Value**: Cuts regulatory response time and improves audit readiness.

---

# Feature Highlights
- Real Gemini 1.5 Flash analysis
- RAG-based evidence grounding
- Executive insights + reasoning panel
- Live processing pipeline UX
- High-risk alert banner + predictive score

---

# Architecture Explanation (Quick)
- **Frontend**: React + Tailwind + Recharts for UI and analytics.
- **Backend**: FastAPI orchestrates PDF parsing, RAG, and agents.
- **AI**: Gemini 1.5 Flash + agent prompts returning structured JSON.
- **Storage**: ChromaDB for vector search, local storage for demo.

---

# Innovation Points
- Agentic regulatory intelligence
- Explainable AI with clause references
- Compliance action point extraction (MAPs)
- Executive exposure summary
- Real-time audit log trail
