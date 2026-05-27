import re
from typing import List, Dict, Any, Optional
from database.database import SessionLocal
from database import models
from rag.hybrid_search import hybrid_search_and_rerank
from services.ai_json import parse_json_with_retry, to_list, get_str
from services.prompt_templates import SYSTEM_PROMPT
from utils.logger import get_logger

logger = get_logger(__name__)

class RetrieverTool:
    """Retrieves relevant semantic chunks for any query and active document context."""
    def run(self, query: str, doc_id: str, regulator: Optional[str] = None) -> List[Dict[str, Any]]:
        logger.info(f"RetrieverTool invoked for query: '{query}'")
        return hybrid_search_and_rerank(query=query, final_k=4, doc_id=doc_id, regulator=regulator)

class RiskScoringTool:
    """Computes mathematical compliance and risk scores dynamically from risk arrays."""
    def run(self, risks: List[Dict[str, Any]]) -> Dict[str, int]:
        logger.info("RiskScoringTool invoked")
        risk_score = 0
        for r in risks:
            sev = str(r.get("severity", "Low")).lower()
            if "high" in sev:
                risk_score += 15
            elif "medium" in sev:
                risk_score += 10
            else:
                risk_score += 5
        
        # Cap risk at 100, compliance score is the inverse
        risk_score = min(100, risk_score)
        compliance_score = max(0, 100 - risk_score)
        return {
            "risk_score": risk_score,
            "compliance_score": compliance_score
        }

class MAPGeneratorTool:
    """Helper tool to structure and parse Measurable Action Points (MAPs) from context."""
    def run(self, context: str) -> List[Dict[str, Any]]:
        logger.info("MAPGeneratorTool invoked")
        from ai_agents.compliance_agent import run_compliance_agent
        result = run_compliance_agent(context)
        return result.get("maps", [])

class DepartmentAssignmentTool:
    """Normalizes and maps keywords to canonical bank department designations."""
    def run(self, raw_department: str) -> str:
        from ai_agents.compliance_agent import _normalize_department
        return _normalize_department(raw_department)

class ComplianceValidationTool:
    """Validates alignment of answers against retrieved context and estimates hallucination risk."""
    def run(self, reply: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("ComplianceValidationTool invoked")
        from services.observability_service import estimate_grounding_quality
        return estimate_grounding_quality(reply, sources)

class KnowledgeGraphTool:
    """Triggers structural updates in the compliance knowledge graph."""
    def run(self, document_id: str) -> Dict[str, Any]:
        logger.info(f"KnowledgeGraphTool updating graph for document: {document_id}")
        from services.graph_service import generate_knowledge_graph
        return generate_knowledge_graph(document_id)

class WorkflowAutomationTool:
    """Automatically persists tasks into SQLite database."""
    def run(self, maps: List[Dict[str, Any]], document_id: str) -> int:
        logger.info(f"WorkflowAutomationTool writing tasks for document: {document_id}")
        from services.task_service import set_tasks_from_maps
        set_tasks_from_maps(maps, document_id)
        return len(maps)

class CrossRegulationComparator:
    """Compares rules across multiple guidelines."""
    def run(self, doc_ids: List[str], query: str) -> Dict[str, Any]:
        logger.info(f"CrossRegulationComparator comparing documents: {doc_ids}")
        from services.cross_document_service import compare_regulations
        return compare_regulations(doc_ids, query)

class AlertGeneratorTool:
    """Persists compliance alerts into SQLite database and triggers WebSockets."""
    def run(self, alerts: List[str], document_id: str) -> int:
        logger.info(f"AlertGeneratorTool writing alerts for document: {document_id}")
        from services.log_service import add_alerts
        add_alerts(alerts, document_id)
        
        # Stream alert updates if possible
        import asyncio
        from api.stream import broadcast_alert
        try:
            loop = asyncio.get_running_loop()
            for alert in alerts:
                loop.create_task(broadcast_alert(alert, "High", document_id=document_id))
        except Exception:
            pass
            
        return len(alerts)
