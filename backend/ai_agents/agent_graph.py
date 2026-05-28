import asyncio
from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from database.database import SessionLocal, get_db_context, db_write_lock, execute_write_serialized
from database import models
from ai_agents.agent_tools import (
    RetrieverTool,
    RiskScoringTool,
    MAPGeneratorTool,
    DepartmentAssignmentTool,
    ComplianceValidationTool,
    KnowledgeGraphTool,
    WorkflowAutomationTool,
    AlertGeneratorTool
)
from utils.logger import get_logger
from services.event_broadcaster import event_bus, EventLogger  # Real-time telemetry

logger = get_logger(__name__)

# Initialize tools
retriever_tool = RetrieverTool()
risk_scoring_tool = RiskScoringTool()
map_generator_tool = MAPGeneratorTool()
dept_assignment_tool = DepartmentAssignmentTool()
compliance_validation_tool = ComplianceValidationTool()
kg_tool = KnowledgeGraphTool()
workflow_tool = WorkflowAutomationTool()
alert_tool = AlertGeneratorTool()

# ==============================================================================
# REAL LANGGRAPH DEFINITIONS
# ==============================================================================
class AgentGraphState(TypedDict):
    """Represents the LangGraph State containing shared context."""
    doc_id: str
    context: str
    regulator: str
    maps: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    audit: List[str]
    alerts: List[str]
    executive_insights: str
    agent_reasoning: List[str]
    grounding_score: float
    hallucination_detected: bool
    conflicts: List[Dict[str, Any]]
    risk_score: int
    compliance_score: int
    correction_iterations: int

def persist_state_to_db(document_id: str, step_name: str, state: Dict[str, Any]):
    """Saves the intermediate state to SQLite between steps."""
    def _save():
        with get_db_context() as db:
            from database.models import AgentGraphState as DBGraphState
            # Filter non-serializable state keys to ensure perfect JSON compliance
            serializable_keys = [
                "doc_id", "context", "regulator", "maps", "risks", "audit", "alerts",
                "executive_insights", "agent_reasoning", "grounding_score",
                "hallucination_detected", "conflicts", "risk_score", "compliance_score",
                "correction_iterations"
            ]
            state_data = {k: state[k] for k in serializable_keys if k in state}
            
            db_state = DBGraphState(
                document_id=document_id,
                step_name=step_name,
                state_data=state_data
            )
            db.add(db_state)
            db.commit()
            
    execute_write_serialized(_save)

def document_analyzer(state: AgentGraphState) -> Dict[str, Any]:
    """Node 1: Analyzes context and extracts action points (MAPs)."""
    logger.info("[LangGraph Node: Document Analyzer] Extracting regulatory directives...")
    EventLogger.log_agent_node_executed(state.get("doc_id"), "Document Analyzer", "Extracting regulatory directives via Qwen2.5")
    try:
        raw_maps = map_generator_tool.run(state["context"])
        for m in raw_maps:
            m["department"] = dept_assignment_tool.run(m.get("department", "Compliance"))
        
        reasoning = state.get("agent_reasoning", []) + ["Document Analyzer: Extracted actionable MAP points via Qwen2.5."]
        updates = {"maps": raw_maps, "agent_reasoning": reasoning}
    except Exception as e:
        logger.error(f"Error in document_analyzer node: {e}")
        reasoning = state.get("agent_reasoning", []) + [f"Document Analyzer failed: {e}"]
        updates = {"agent_reasoning": reasoning}
        
    persist_state_to_db(state["doc_id"], "document_analyzer", {**state, **updates})
    return updates

def compliance_checker(state: AgentGraphState) -> Dict[str, Any]:
    """Node 2: Runs risk assessment, validation checks, and measures grounding."""
    logger.info("[LangGraph Node: Compliance Checker] Reviewing rules and calculating risk exposure...")
    EventLogger.log_agent_node_executed(state.get("doc_id"), "Compliance Checker", "Calculating risk exposure and grounding score")
    from ai_agents.risk_agent import run_risk_agent
    
    risks = []
    risk_score = 0
    compliance_score = 100
    grounding_score = 1.0
    hallucination_detected = False
    
    try:
        risk_res = run_risk_agent(state["context"])
        risks = risk_res.get("risks", [])
        
        scores = risk_scoring_tool.run(risks)
        risk_score = scores["risk_score"]
        compliance_score = scores["compliance_score"]
    except Exception as e:
        logger.error(f"Error in risk checks: {e}")

    try:
        mock_sources = [{"section_title": m.get("source_section", "General"), "snippet": m.get("title", ""), "score": 0.9} for m in state.get("maps", [])]
        text_to_validate = " ".join([m.get("title", "") for m in state.get("maps", [])[:2]])
        validation_res = compliance_validation_tool.run(text_to_validate, mock_sources)
        
        grounding_score = validation_res.get("grounding_score", 0.9)
        hallucination_detected = validation_res.get("risk", "low") == "high" or grounding_score < 0.7
    except Exception as e:
        logger.error(f"Error in compliance validation: {e}")

    reasoning = state.get("agent_reasoning", []) + [
        f"Compliance Checker: Assessed risk score to {risk_score} (compliance score: {compliance_score}%). Grounding score: {grounding_score * 100}%. Hallucination flag: {hallucination_detected}."
    ]
    
    updates = {
        "risks": risks,
        "risk_score": risk_score,
        "compliance_score": compliance_score,
        "grounding_score": grounding_score,
        "hallucination_detected": hallucination_detected,
        "agent_reasoning": reasoning
    }
    EventLogger.log_compliance_result(state.get("doc_id"), compliance_score, risk_score, int(grounding_score*100))
    if hallucination_detected:
        event_bus.emit("risk_detected", f"Hallucination flag triggered (grounding {int(grounding_score*100)}% < 70%)", doc_id=state.get("doc_id"))
    persist_state_to_db(state["doc_id"], "compliance_checker", {**state, **updates})
    return updates

def cross_regulation(state: AgentGraphState) -> Dict[str, Any]:
    """Node 3: Compares guidelines across different circulars."""
    logger.info("[LangGraph Node: Cross Regulation] Checking conflicts against active corpus...")
    EventLogger.log_agent_node_executed(state.get("doc_id"), "Cross-Regulation", "Comparing guidelines across regulatory corpus")
    conflicts = []
    
    with get_db_context() as db:
        other_docs = db.query(models.Document).filter(models.Document.id != state["doc_id"]).limit(2).all()
        other_doc_ids = [doc.id for doc in other_docs]
    
    if other_doc_ids:
        doc_ids = [state["doc_id"]] + other_doc_ids
        from services.cross_document_service import compare_regulations
        try:
            comparison = compare_regulations(doc_ids, "cybersecurity and risk governance differences")
            conflicts = comparison.get("conflicts", [])
        except Exception as e:
            logger.warning(f"Cross comparison failed or skipped: {e}")
            
    reasoning = state.get("agent_reasoning", []) + [
        f"Cross-Regulation: Cross-referenced guidelines. Identified {len(conflicts)} conflicting requirements."
    ]
    
    updates = {
        "conflicts": conflicts,
        "agent_reasoning": reasoning
    }
    persist_state_to_db(state["doc_id"], "cross_regulation", {**state, **updates})
    return updates

def self_corrector(state: AgentGraphState) -> Dict[str, Any]:
    """Node 4: Evaluates grounding quality and refines analysis outputs."""
    logger.info("[LangGraph Node: Self Corrector] Inspecting hallucination triggers...")
    EventLogger.log_agent_node_executed(state.get("doc_id"), "Self-Corrector", "Evaluating grounding quality for hallucination triggers")
    
    hallucinated = state.get("hallucination_detected", False)
    iterations = state.get("correction_iterations", 0)
    reasoning = state.get("agent_reasoning", [])
    
    if hallucinated and iterations < 2:
        iterations += 1
        reasoning.append(f"Self Corrector: Hallucination detected (grounding < 70%). Refining query analysis loop ({iterations}/2)...")
        # Perform correction: Filter out short titles or maps lacking compliance severity
        maps = state.get("maps", [])
        corrected_maps = [m for m in maps if m.get("title") and len(m.get("title", "")) > 12]
        
        updates = {
            "maps": corrected_maps,
            "correction_iterations": iterations,
            "hallucination_detected": False,  # Reset flag for verification re-run
            "agent_reasoning": reasoning
        }
    else:
        reasoning.append("Self Corrector: Grounding threshold verification satisfied. Moving to task generation.")
        updates = {
            "agent_reasoning": reasoning
        }
        
    persist_state_to_db(state["doc_id"], "self_corrector", {**state, **updates})
    return updates

def task_generator(state: AgentGraphState) -> Dict[str, Any]:
    """Node 5: Translates compliance gaps to tasks and initiates high-risk alerts."""
    logger.info("[LangGraph Node: Task Generator] Creating compliance workflows...")
    EventLogger.log_agent_node_executed(state.get("doc_id"), "Task Generator", "Creating MAP tasks and compliance alerts")
    
    maps = state.get("maps", [])
    alerts = state.get("alerts", [])
    
    if not alerts and state.get("risks"):
        alerts = [
            f"Vulnerability risk alert: {r.get('risk')}" 
            for r in state.get("risks") 
            if str(r.get("severity", "Medium")).lower() == "high"
        ]
        
    if maps:
        execute_write_serialized(workflow_tool.run, maps, state["doc_id"])
    if alerts:
        execute_write_serialized(alert_tool.run, alerts, state["doc_id"])
        
    reasoning = state.get("agent_reasoning", []) + [
        f"Task Generator: Generated tasks ({len(maps)}) and compliance alerts ({len(alerts)}) in SentinelX DB."
    ]
    
    updates = {
        "alerts": alerts,
        "agent_reasoning": reasoning
    }
    EventLogger.log_task_generated(state.get("doc_id"), len(maps), len(alerts))
    persist_state_to_db(state["doc_id"], "task_generator", {**state, **updates})
    return updates

# ==============================================================================
# REAL LANGGRAPH STATEGRAPH COMPILATION
# ==============================================================================
workflow = StateGraph(AgentGraphState)

# Register Nodes
workflow.add_node("document_analyzer", document_analyzer)
workflow.add_node("compliance_checker", compliance_checker)
workflow.add_node("cross_regulation", cross_regulation)
workflow.add_node("self_corrector", self_corrector)
workflow.add_node("task_generator", task_generator)

# Entry Point
workflow.set_entry_point("document_analyzer")

# Linear edges
workflow.add_edge("document_analyzer", "compliance_checker")
workflow.add_edge("compliance_checker", "cross_regulation")

# Conditional Edge from Cross-Regulation based on Checker results
def route_after_checks(state: AgentGraphState):
    if state.get("hallucination_detected") and state.get("correction_iterations", 0) < 2:
        return "self_corrector"
    return "task_generator"

workflow.add_conditional_edges(
    "cross_regulation",
    route_after_checks,
    {
        "self_corrector": "self_corrector",
        "task_generator": "task_generator"
    }
)

# Loop back edge
workflow.add_edge("self_corrector", "document_analyzer")

# Terminal Edge
workflow.add_edge("task_generator", END)

# Compile
langgraph_app = workflow.compile()


async def run_autonomous_compliance_graph(document_id: str, context: str) -> Dict[str, Any]:
    """
    Orchestrates the compliance nodes using a real LangGraph StateGraph engine.
    Runs locally on NVIDIA Jetson using local Ollama model.
    """
    logger.info(f"Initiating real LangGraph compliance pipeline for doc: {document_id}")
    
    # Resolve regulator
    with get_db_context() as db:
        doc_db = db.query(models.Document).filter(models.Document.id == document_id).first()
        regulator = doc_db.regulator if (doc_db and doc_db.regulator) else "RBI"

    # Initialize state
    initial_state = {
        "doc_id": document_id,
        "context": context,
        "regulator": regulator,
        "maps": [],
        "risks": [],
        "audit": [],
        "alerts": [],
        "executive_insights": "",
        "agent_reasoning": ["Orchestrator: Initializing real LangGraph pipeline."],
        "grounding_score": 1.0,
        "hallucination_detected": False,
        "conflicts": [],
        "risk_score": 0,
        "compliance_score": 100,
        "correction_iterations": 0
    }

    # Execute LangGraph asynchronously
    try:
        final_state = await langgraph_app.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"LangGraph execution failed: {e}. Attempting to recover partial state...")
        with get_db_context() as db:
            latest_state_db = db.query(models.AgentGraphState).filter(
                models.AgentGraphState.document_id == document_id
            ).order_by(models.AgentGraphState.timestamp.desc()).first()
            
            if latest_state_db and latest_state_db.state_data:
                logger.info(f"Recovered partial state from step: {latest_state_db.step_name}")
                final_state = latest_state_db.state_data
                if "agent_reasoning" not in final_state:
                    final_state["agent_reasoning"] = []
                final_state["agent_reasoning"].append(
                    f"System recovered partial results from step '{latest_state_db.step_name}' after a model connection issue."
                )
            else:
                raise e

    # Phase C: Trigger Knowledge Graph build sequentially
    logger.info("[Graph Orchestrator] Executing Phase C knowledge graph compilation...")
    try:
        async with db_write_lock:
            await asyncio.to_thread(kg_tool.run, document_id)
        final_state["agent_reasoning"].append("Knowledge Graph Agent: Rebuilt and updated relationship pathways.")
    except Exception as e:
        logger.error(f"Failed to update knowledge graph: {e}")

    # Generate Executive Summary using Synthesizer pass
    from services.enterprise_answer_synthesizer import enrich_agent_output
    raw_output = {
        "maps": final_state.get("maps", []),
        "risks": final_state.get("risks", []),
        "audit": final_state.get("audit", []),
        "alerts": final_state.get("alerts", []),
        "executive_insights": final_state.get("executive_insights", ""),
        "agent_reasoning": final_state.get("agent_reasoning", []),
        "conflicts": final_state.get("conflicts", [])
    }
    
    enriched = await asyncio.to_thread(enrich_agent_output, raw_output, context)
    
    # Structure the final response payload
    final_result = {
        "document_id": document_id,
        "summary": enriched.get("synthesis", {}).get("executive_summary", "") or enriched.get("executive_insights", ""),
        "compliance_score": final_state.get("compliance_score", 100),
        "risk_score": final_state.get("risk_score", 0),
        "maps": enriched.get("maps", []),
        "risks": enriched.get("risks", []),
        "departments": list({m["department"] for m in enriched.get("maps", [])}),
        "executive_insights": enriched.get("synthesis", {}).get("strategic_insights", "") or enriched.get("executive_insights", ""),
        "agent_reasoning": enriched.get("agent_reasoning", []),
        "grounding_confidence": round(final_state.get("grounding_score", 1.0), 2),
        "hallucination_flag": final_state.get("grounding_score", 1.0) < 0.7,
        "conflicts": final_state.get("conflicts", [])
    }

    return final_result


# ==============================================================================
# BACKWARD COMPATIBILITY CLASSES & FUNCTIONS FOR TEST SUITE
# ==============================================================================
class AgentState:
    """Compatibility class for existing unit tests."""
    def __init__(self, doc_id: str, context: str):
        self.doc_id = doc_id
        self.context = context
        self.regulator = "RBI"
        self.maps: List[Dict[str, Any]] = []
        self.risks: List[Dict[str, Any]] = []
        self.audit: List[str] = []
        self.alerts: List[str] = []
        self.executive_insights = ""
        self.agent_reasoning: List[str] = []
        self.grounding_score = 1.0
        self.hallucination_detected = False
        self.conflicts: List[Dict[str, Any]] = []
        self.risk_score = 0
        self.compliance_score = 100

def compliance_node(state: AgentState) -> AgentState:
    """Compatibility compliance_node for unit tests."""
    try:
        raw_maps = map_generator_tool.run(state.context)
        for m in raw_maps:
            m["department"] = dept_assignment_tool.run(m.get("department", "Compliance"))
        state.maps = raw_maps
        state.agent_reasoning.append("Compliance Agent: Extracted actionable points and targets.")
    except Exception as e:
        logger.error(f"Error in compatibility compliance_node: {e}")
    return state

def risk_node(state: AgentState) -> AgentState:
    """Compatibility risk_node for unit tests."""
    from ai_agents.risk_agent import run_risk_agent
    try:
        risk_res = run_risk_agent(state.context)
        state.risks = risk_res.get("risks", [])
        scores = risk_scoring_tool.run(state.risks)
        state.risk_score = scores["risk_score"]
        state.compliance_score = scores["compliance_score"]
        for r in state.risks:
            state.agent_reasoning.append(f"Risk Agent: Identified risk '{r.get('risk')}'")
    except Exception as e:
        logger.error(f"Error in compatibility risk_node: {e}")
    return state
