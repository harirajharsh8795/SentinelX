"""
Phase 10 — Knowledge Graph Intelligence
Document-aware, source-linked, relationship-aware graph with risk propagation.
"""
import json
from typing import Any, Dict, List, Optional

from vector_db.chroma_client import get_client
from utils.gemini import generate_text
from utils.logger import get_logger
from services.ai_json import parse_json_with_retry, to_list, get_str
from database.database import SessionLocal
from database.models import Document, Task

logger = get_logger(__name__)

NODE_COLORS = {
    "Document": "#A49970",
    "Department": "#00E5FF",
    "Rule": "#7C3AED",
    "Action": "#F6D365",
    "Penalty": "#FF4B4B",
    "Risk": "#FF6B35",
}

SEVERITY_PROPAGATION = {"High": 1.0, "Medium": 0.6, "Low": 0.3}


def _get_document_chunks(document_id: str) -> List[Dict[str, Any]]:
    client = get_client()
    collection = client.get_or_create_collection(name="canara_sentinel_v4")
    results = collection.get(
        where={"doc_id": document_id},
        include=["documents", "metadatas"],
    )
    docs = results.get("documents", []) or []
    metas = results.get("metadatas", []) or []
    chunks = []
    for text, meta in zip(docs, metas):
        chunks.append({
            "text": text,
            "section_title": (meta or {}).get("section_title", "General"),
            "chunk_index": (meta or {}).get("chunk_index", 0),
            "regulator": (meta or {}).get("regulator"),
            "framework": (meta or {}).get("framework"),
        })
    return chunks


def _enrich_nodes_with_sources(nodes: List[dict], chunks: List[dict]) -> List[dict]:
    """Attach best-matching source snippet to each node by label keyword overlap."""
    for node in nodes:
        label_words = set(node.get("label", "").lower().split())
        best = None
        best_score = 0
        for ch in chunks:
            text_lower = ch["text"].lower()
            score = sum(1 for w in label_words if len(w) > 3 and w in text_lower)
            if score > best_score:
                best_score = score
                best = ch
        if best:
            node["source_section"] = best["section_title"]
            node["source_snippet"] = best["text"][:300]
            node["chunk_index"] = best["chunk_index"]
    return nodes


def _compute_risk_propagation(nodes: List[dict], edges: List[dict]) -> List[dict]:
    """
    Propagate risk scores from Risk nodes through the graph (BFS-style).
    """
    risk_nodes = {n["id"]: n for n in nodes if n.get("type") == "Risk"}
    if not risk_nodes:
        return nodes

    adjacency: Dict[str, List[str]] = {}
    for e in edges:
        adjacency.setdefault(e["source"], []).append(e["target"])
        adjacency.setdefault(e["target"], []).append(e["source"])

    for node in nodes:
        if node.get("type") == "Risk":
            sev = node.get("severity", "Medium")
            node["risk_score"] = SEVERITY_PROPAGATION.get(sev, 0.5)
            node["propagation_level"] = 0
        else:
            node["risk_score"] = 0.0
            node["propagation_level"] = -1

    queue = [(nid, risk_nodes[nid].get("risk_score", 0.5), 0) for nid in risk_nodes]
    visited_prop = set()

    while queue:
        current_id, score, level = queue.pop(0)
        if current_id in visited_prop and level > 0:
            continue
        visited_prop.add(current_id)

        for neighbor_id in adjacency.get(current_id, []):
            neighbor = next((n for n in nodes if n["id"] == neighbor_id), None)
            if not neighbor:
                continue
            decayed = score * 0.7
            if decayed > neighbor.get("risk_score", 0):
                neighbor["risk_score"] = round(decayed, 2)
                neighbor["propagation_level"] = level + 1
                if level < 3:
                    queue.append((neighbor_id, decayed, level + 1))

    return nodes


def _inject_task_actions(nodes: List[dict], edges: List[dict], document_id: str) -> tuple:
    """Add Action nodes from DB tasks linked to this document."""
    from database.database import get_db_context
    with get_db_context() as db:
        tasks = db.query(Task).filter(Task.document_id == document_id).limit(10).all()
        task_data = [{"id": t.id, "title": t.title, "priority": t.priority, "department": t.department, "deadline": t.deadline, "status": t.status} for t in tasks]

    for task in task_data:
        node_id = f"task_{task['id'][:8]}"
        nodes.append({
            "id": node_id,
            "label": task["title"][:60],
            "type": "Action",
            "severity": task["priority"],
            "department": task["department"],
            "source_section": "MAP Task",
            "source_snippet": f"Department: {task['department']}, Deadline: {task['deadline']}",
            "status": task["status"],
        })
        dept_node = next((n for n in nodes if n.get("type") == "Department" and task["department"].lower() in n.get("label", "").lower()), None)
        if dept_node:
            edges.append({"source": dept_node["id"], "target": node_id, "label": "assigned_action", "weight": 1.0})
    return nodes, edges


_graph_cache = {}


def generate_knowledge_graph(document_id: str) -> dict:
    from database.database import get_db_context
    
    # Quick in-memory cache check
    if document_id in _graph_cache:
        return _graph_cache[document_id]
    
    with get_db_context() as db:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc and doc.knowledge_graph:
            try:
                if isinstance(doc.knowledge_graph, str):
                    res = json.loads(doc.knowledge_graph)
                elif isinstance(doc.knowledge_graph, dict):
                    res = doc.knowledge_graph
                _graph_cache[document_id] = res
                return res
            except Exception as e:
                logger.warning(f"Error loading cached knowledge_graph JSON: {e}")

    chunks = _get_document_chunks(document_id)
    if not chunks:
        return {
            "document_id": document_id,
            "nodes": [],
            "edges": [],
            "risk_summary": {"high_risk_nodes": 0, "max_propagation": 0},
        }

    context_text = "\n\n".join(
        f"[Section: {c['section_title']}]\n{c['text'][:800]}" for c in chunks[:8]
    )

    with get_db_context() as db:
        doc = db.query(Document).filter(Document.id == document_id).first()
        doc_label = doc.filename if doc else "Regulatory Document"
        regulator = doc.regulator if doc else None
        framework = doc.framework if doc else None

    prompt = f"""You are a Compliance Knowledge Graph architect.
Extract entities and relationships from the document. Include Risk nodes for compliance risks.

Return ONLY valid JSON:
{{
  "nodes": [
    {{"id": "doc_1", "label": "{doc_label}", "type": "Document", "severity": null}},
    {{"id": "risk_1", "label": "KYC breach risk", "type": "Risk", "severity": "High"}},
    {{"id": "rule_1", "label": "Section 3.2 KYC", "type": "Rule", "severity": null}},
    {{"id": "dep_1", "label": "Compliance Department", "type": "Department", "severity": null}},
    {{"id": "act_1", "label": "Update KYC policy", "type": "Action", "severity": "High"}},
    {{"id": "pen_1", "label": "Monetary penalty", "type": "Penalty", "severity": "High"}}
  ],
  "edges": [
    {{"source": "doc_1", "target": "rule_1", "label": "contains", "weight": 1.0}},
    {{"source": "rule_1", "target": "dep_1", "label": "applies_to", "weight": 1.0}},
    {{"source": "rule_1", "target": "act_1", "label": "requires_action", "weight": 1.0}},
    {{"source": "risk_1", "target": "dep_1", "label": "threatens", "weight": 0.9}},
    {{"source": "act_1", "target": "pen_1", "label": "has_penalty", "weight": 0.8}}
  ]
}}

Node types: Document, Department, Rule, Action, Penalty, Risk.
Edge labels: applies_to, requires_action, has_penalty, reports_to, threatens, contains.

DOCUMENT:
{context_text[:10000]}
"""
    data = parse_json_with_retry(prompt, schema_hint="nodes and edges arrays")
    nodes = []
    for item in to_list(data.get("nodes")):
        if isinstance(item, dict) and item.get("id"):
            nodes.append({
                "id": get_str(item.get("id")),
                "label": get_str(item.get("label")),
                "type": get_str(item.get("type"), "Rule"),
                "severity": item.get("severity"),
                "color": NODE_COLORS.get(get_str(item.get("type")), "#FFFFFF"),
            })

    edges = []
    for item in to_list(data.get("edges")):
        if isinstance(item, dict) and item.get("source") and item.get("target"):
            edges.append({
                "source": get_str(item.get("source")),
                "target": get_str(item.get("target")),
                "label": get_str(item.get("label"), "relates_to"),
                "weight": float(item.get("weight", 1.0)),
            })

    nodes = _enrich_nodes_with_sources(nodes, chunks)
    nodes, edges = _inject_task_actions(nodes, edges, document_id)
    nodes = _compute_risk_propagation(nodes, edges)

    high_risk = [n for n in nodes if n.get("risk_score", 0) >= 0.6]
    max_prop = max((n.get("propagation_level", 0) for n in nodes), default=0)

    # 4. Trace Cascading compliance risk paths
    cascading_risk_paths = []
    node_by_id = {n["id"]: n for n in nodes}
    for edge in edges:
        s = node_by_id.get(edge["source"])
        t = node_by_id.get(edge["target"])
        if s and t:
            # Check for Action / Rule -> Risk / Penalty chain
            if s.get("type") in ("Action", "Rule") and t.get("type") in ("Risk", "Penalty"):
                cascading_risk_paths.append({
                    "trigger_node": s["label"],
                    "threatened_node": t["label"],
                    "relation": edge["label"],
                    "risk_propagation_score": round(s.get("risk_score", 0.5) * edge.get("weight", 1.0), 2)
                })

    result_dict = {
        "document_id": document_id,
        "document_name": doc_label,
        "regulator": regulator,
        "framework": framework,
        "nodes": nodes,
        "edges": edges,
        "risk_summary": {
            "high_risk_nodes": len(high_risk),
            "max_propagation": max_prop,
            "top_risks": [
                {"id": n["id"], "label": n["label"], "risk_score": n.get("risk_score", 0)}
                for n in sorted(nodes, key=lambda x: x.get("risk_score", 0), reverse=True)[:5]
                if n.get("type") == "Risk" or n.get("risk_score", 0) > 0.3
            ],
            "cascading_risk_paths": cascading_risk_paths[:6]
        },
    }

    with get_db_context() as db:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.knowledge_graph = result_dict
            db.commit()

    _graph_cache[document_id] = result_dict
    return result_dict


def get_node_detail(document_id: str, node_id: str) -> Optional[dict]:
    graph = generate_knowledge_graph(document_id)
    node = next((n for n in graph["nodes"] if n["id"] == node_id), None)
    if not node:
        return None

    connected = []
    for e in graph["edges"]:
        if e["source"] == node_id:
            target = next((n for n in graph["nodes"] if n["id"] == e["target"]), None)
            if target:
                connected.append({"direction": "outgoing", "edge": e["label"], "node": target})
        elif e["target"] == node_id:
            source = next((n for n in graph["nodes"] if n["id"] == e["source"]), None)
            if source:
                connected.append({"direction": "incoming", "edge": e["label"], "node": source})

    return {"node": node, "connections": connected, "document_id": document_id}
