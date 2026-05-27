from ai_agents.compliance_agent import run_compliance_agent
from ai_agents.risk_agent import run_risk_agent
from ai_agents.audit_agent import run_audit_agent
from ai_agents.notification_agent import run_notification_agent
from ai_agents.executive_agent import run_executive_agent
from services.enterprise_answer_synthesizer import merge_retrieved_context, enrich_agent_output


def run_agents(context: str) -> dict:
    # Phase 3: deduplicate and merge context before agent execution
    if "---" in context or "[Source" in context:
        raw_chunks = [c.strip() for c in context.split("---") if c.strip()]
        context = merge_retrieved_context(raw_chunks)

    compliance = run_compliance_agent(context)
    risk = run_risk_agent(context)
    audit = run_audit_agent(context)
    notification = run_notification_agent(context)
    executive = run_executive_agent(context)

    raw_output = {
        "maps": compliance["maps"],
        "risks": risk["risks"],
        "audit": audit["audit"],
        "alerts": notification["alerts"],
        "executive_insights": executive["executive_insights"],
        "agent_reasoning": (
            compliance["reasoning"] + risk["reasoning"] + audit["reasoning"] + executive["reasoning"]
        ),
    }

    # Phase 3: enterprise synthesis pass on combined agent outputs
    return enrich_agent_output(raw_output, context)
