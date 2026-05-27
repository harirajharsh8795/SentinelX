"""
Phase 3 — Enterprise Synthesis Engine
Merges retrieved chunks, deduplicates context, and synthesizes agent outputs
into executive-ready intelligence.
"""
from typing import Any, Dict, List
import hashlib

from services.gemini_service import generate_text
from services.ai_json import parse_json_with_retry, get_str, to_list


def _chunk_fingerprint(text: str) -> str:
    normalized = " ".join(text.split()).lower()[:500]
    return hashlib.md5(normalized.encode()).hexdigest()


def deduplicate_chunks(chunks: List[str]) -> List[str]:
    """Remove near-duplicate context blocks before sending to agents."""
    seen = set()
    unique = []
    for chunk in chunks:
        fp = _chunk_fingerprint(chunk)
        if fp not in seen:
            seen.add(fp)
            unique.append(chunk)
    return unique


def merge_retrieved_context(chunks: List[str], max_chars: int = 12000) -> str:
    """
    Merge and trim retrieved chunks into a single coherent context block.
    Preserves section headers for citation traceability.
    """
    deduped = deduplicate_chunks(chunks)
    merged = []
    total = 0
    for chunk in deduped:
        if total + len(chunk) > max_chars:
            remaining = max_chars - total
            if remaining > 200:
                merged.append(chunk[:remaining] + "\n[...truncated]")
            break
        merged.append(chunk)
        total += len(chunk)
    return "\n\n---\n\n".join(merged)


def synthesize_executive_summary(
    maps: List[dict],
    risks: List[dict],
    context_preview: str,
) -> Dict[str, Any]:
    """
    Phase 7: Generate DISTINCT executive summary and strategic insights,
    plus business impact and structured risk explanations.
    """
    maps_summary = "\n".join(
        f"- {m.get('title', 'N/A')} [{m.get('department', 'General')}] "
        f"deadline={m.get('deadline', 'N/A')} severity={m.get('severity', 'Medium')}"
        for m in maps[:8]
    ) or "No MAPs extracted."
    risks_summary = "\n".join(
        f"- {r.get('risk', 'N/A')} [{r.get('severity', 'Low')}]"
        for r in risks[:8]
    ) or "No risks identified."

    prompt = f"""You are an enterprise regulatory intelligence synthesizer for SentinelX.
Based on the extracted compliance data below, produce a board-ready synthesis.

Return ONLY valid JSON:
{{
  "executive_summary": "Provide a high-quality executive intelligence summary. Format it strictly to contain:\\n- A short intelligence overview of the regulatory circular.\\n- The total number of directives ({len(maps)} directives identified).\\n- List of affected departments.\\n- Key compliance severity level.\\n- Current operational status (e.g. 'Operationally Ready' or 'Under Review').",
  "strategic_insights": "Provide strategic compliance insights. Format it strictly as follows (using markdown formatting for headers):\\n\\n**Business Implications**\\n[Describe the business implications here]\\n\\n**Governance Responsibilities**\\n[Describe governance responsibilities here]\\n\\n**Operational Recommendations**\\n[Describe operational recommendations here]\\n\\n**Compliance Exposure Analysis**\\n[Describe exposure analysis here]\\n\\n**Strategic Actions**\\n[List priority strategic actions here]",
  "business_impact": "Bullet-style impact on operations, capital, reputation",
  "risk_explanations": [
    {{"risk": "...", "severity": "High|Medium|Low", "explanation": "why this matters", "mitigation": "recommended action"}}
  ],
  "priority_actions": ["top 3 actions in order of urgency"]
}}

--- EXTRACTED MAPs ---
{maps_summary}

--- EXTRACTED RISKS ---
{risks_summary}

--- DOCUMENT CONTEXT PREVIEW ---
{context_preview[:2000]}
"""
    data = parse_json_with_retry(prompt, schema_hint="executive_summary, strategic_insights, business_impact, risk_explanations, priority_actions")

    risk_explanations = []
    for item in to_list(data.get("risk_explanations")):
        if isinstance(item, dict):
            risk_explanations.append({
                "risk": get_str(item.get("risk")),
                "severity": get_str(item.get("severity"), "Medium"),
                "explanation": get_str(item.get("explanation")),
                "mitigation": get_str(item.get("mitigation")),
            })

    return {
        "executive_summary": get_str(data.get("executive_summary")),
        "strategic_insights": get_str(data.get("strategic_insights")),
        "business_impact": get_str(data.get("business_impact")),
        "risk_explanations": risk_explanations,
        "priority_actions": [get_str(a) for a in to_list(data.get("priority_actions")) if get_str(a)],
    }


def enrich_agent_output(agent_output: dict, context: str) -> dict:
    """
    Full synthesis pipeline: enrich raw agent outputs with executive intelligence.
    """
    synthesis = synthesize_executive_summary(
        agent_output.get("maps", []),
        agent_output.get("risks", []),
        context[:3000],
    )

    executive_text = synthesis["executive_summary"]
    if synthesis["business_impact"]:
        executive_text += f"\n\n**Business Impact:** {synthesis['business_impact']}"

    reasoning = list(agent_output.get("agent_reasoning", []))
    for action in synthesis.get("priority_actions", [])[:3]:
        reasoning.append(f"Priority Action: {action}")

    enriched_risks = []
    risk_lookup = {r.get("risk", ""): r for r in agent_output.get("risks", [])}
    for expl in synthesis.get("risk_explanations", []):
        base = risk_lookup.get(expl["risk"], {})
        enriched_risks.append({
            **base,
            "risk": expl["risk"] or base.get("risk", ""),
            "severity": expl["severity"] or base.get("severity", "Medium"),
            "reason": expl["explanation"] or base.get("reason", ""),
            "mitigation": expl.get("mitigation", ""),
            "source_section": base.get("source_section", ""),
        })

    if not enriched_risks:
        enriched_risks = agent_output.get("risks", [])

    return {
        **agent_output,
        "executive_insights": executive_text,
        "risks": enriched_risks,
        "agent_reasoning": reasoning,
        "synthesis": synthesis,
    }
