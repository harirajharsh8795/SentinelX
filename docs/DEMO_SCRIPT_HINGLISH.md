# EdgeMinds Hackathon: SentinelX 5-Minute Demo Script (Hinglish)

Yeh script EdgeMinds judges ke samne dynamic, high-impact presentation dene ke liye design kiya gaya hai. Isme aapki system ke main strengths—**Real-Time Telemetry via WebSockets**, **Real LangGraph Orchestration**, aur **Knowledge Graph Visualization**—ko showcase kiya gaya hai.

---

## ⏱️ Timeline Overview (Total: 5 Minutes)
- **0:00 - 0:45 (45s)**: Hook & Opening (System Setup & Live Dashboard Overview)
- **0:45 - 2:00 (75s)**: Document Ingestion & Live WebSocket Telemetry Stream
- **2:00 - 3:15 (75s)**: LangGraph Node Execution, Compliance Scores & Risk Analysis
- **3:15 - 4:30 (75s)**: Explaining the Knowledge Graph & Task Workflows
- **4:30 - 5:00 (30s)**: Closing Pitch & Q&A Hook

---

## 🎤 The Demo Script

### 1. Hook & Opening (0:00 - 0:45)
**Screen to Show**: Dashboard (`/dashboard`) showing live system telemetry, system exposure trend line, and the "SYSTEM ONLINE" blinking green badge.

**What to Say (Hinglish)**:
> "Good morning judges! Hum jab bhi banking compliance ki baat karte hain, toh sabse bada pain point hota hai—frequent regulatory circulars ko manually padhna, analyze karna aur implementation gap ko track karna.
> 
> Meet **SentinelX**—hamara Autonomous AI Compliance system jo complex regulatory documents ko actionable compliance workflows aur measurable action points (MAPs) mein convert karta hai.
> 
> Abhi aap screen par humara main **Enterprise Intelligence Dashboard** dekh rahe hain. Top right corner par aap **SYSTEM ONLINE** live heart-beat signal dekh sakte hain aur side mein humari **AI Telemetry Feed** hai. Yeh koi static mock text nahi hai! Yeh direct FastAPI event loop se WebSocket connection ke through server ke real-time operations ko feed kar raha hai. Jaise hi hum backend pe koi action perform karenge, aapko yahan real-time system logs aate dikhenge."

---

### 2. Document Ingestion & Live Telemetry (0:45 - 2:00)
**Screen to Show**: Upload Page (`/upload`) and then switch back to Dashboard (`/dashboard`) or watch the Sidebar alerts.

**What to Say (Hinglish)**:
> "Ab hum compliance check demonstrate karne ke liye ek real document ingest karenge. Hum upload karenge **CYBERSECURITYRBI.pdf** (RBI Cyber Security Framework Circular) jo ki humare `PDF FOR TEST` folder mein hai.
> 
> *[Perform PDF upload on UI]*
> 
> Jaise hi main is PDF ko upload karta hoon, humara backend direct parser aur text chunking engine ko trigger kar deta hai. Let's switch back to the Dashboard to see what is happening under the hood!
> 
> Look at the **AI Telemetry feed** right here:
> - **[EMBED]** Vector embedding started: Generating chunks...
> - **[UPLOAD]** Circular text uploaded successfully.
> - **[EMBED]** ChromaDB indexing complete: Vector store populated.
> 
> Yeh pure process ki telemetry details live WebSockets ke through reflect ho rahi hain, with exact UTC timestamps. Isse compliance officer ko complete operational visibility milti hai."

---

### 3. LangGraph Node Execution & Compliance Scores (2:00 - 3:15)
**Screen to Show**: Document Analysis Page (`/analysis`) and Agent Logs (`/agent-logs`).

**What to Say (Hinglish)**:
> "Ab aate hain hamare brain par—**LangGraph Orchestration**. EdgeMinds ke Track 3 ke guidelines ke mutabik, SentinelX ek multi-agent graph run karta hai local Small Language Model (SLM - Qwen 2.5) ko use karke.
> 
> Jab hum **Analysis Page** par chalenge, toh hum dekh sakte hain ki hamari AI ne pooray document ko cross-examine kiya hai. Humare graph mein 4 key nodes sequential aur conditional loops run karte hain:
> 1. **Document Analyzer**: Jisne document se regulatory requirements ko extract kiya.
> 2. **Compliance Checker**: Jo risk aur grounding score evaluate karta hai.
> 3. **Self-Corrector**: Agar output ka grounding confidence low hai, toh loop automatically self-correct karta hai.
> 4. **Task Generator**: Jo automatic tasks generate karta hai database mein.
> 
> Yahan aap compliance summary dekh sakte hain: **Risk Score: 78%**, **Compliance Score: 85%**, aur **Grounding Score: 92%**. Humein pure citations milte hain—yani AI ne koi hallucination nahi kiya hai, target clauses are linked directly to source paragraphs."

---

### 4. Explaining the Knowledge Graph & Querying (3:15 - 4:30)
**Screen to Show**: Knowledge Graph Page (`/knowledge-graph`) and Chat Interface (`/chat`).

**What to Say (Hinglish)**:
> "Compliance analysis ke baad sabse badhi problem hoti hai relationship and impact mapping. SentinelX isse resolve karta hai humare interactive **Knowledge Graph** visualization se.
> 
> *[Show Knowledge Graph]*
> 
> Is graph mein center nodes regulatory circulars ko represent karte hain, aur connected nodes are different departments (like Cybersecurity, IT Risk, Operations) aur rules. Agar RBI kal cyber risk framework mein changes karti hai, toh graph instantly highlight kar deta hai ki humare bank ka kaun-kaun sa department aur existing guidelines impact honge. 
> 
> Let's test the interactive chat tool by asking a query: 
> *'What are the mandatory logging requirements for user access controls?'*
> 
> *[Type and ask query in Chat]*
> 
> Humara hybrid RAG engine ChromaDB se source retrieval karke model ko feed karega aur direct answer generate karega with reference guidelines, alerts, aur tasks."

---

### 5. Closing Pitch & Q&A Hook (4:30 - 5:00)
**Screen to Show**: Dashboard showing updated statistics (Compliance score updated, Tasks generated).

**What to Say (Hinglish)**:
> "To wrap up: SentinelX compliance and auditing ko manual risk se shift karke autonomous continuous monitoring pe lata hai. With real-time WebSockets, real-time telemetry, and multi-agent LangGraph workflows, hum banks ko software audit ready rakhte hain without any human delay.
> 
> SentinelX is **Fast, Audit-Grade, and Local**—running completely inside a low-resource NVIDIA Jetson edge platform.
> 
> Thank you so much judges! Now, I am open to any technical questions about our LangGraph state machine, ChromaDB hybrid search, or WebSocket telemetry implementation."

---
