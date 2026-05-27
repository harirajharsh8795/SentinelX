from services.ai_json import parse_json_with_retry, to_list, get_str


def run_risk_agent(context: str) -> dict:
    prompt = (
        "You are a banking risk analyst. Return ONLY valid JSON. "
        "Schema: {\"risks\":[{\"risk\",\"severity\",\"reason\",\"source_section\"}],"
        "\"reasoning\":[\"...\"]}. Identify compliance risks from the context.\n"
        "Context:\n" + context
    )
    data = parse_json_with_retry(prompt, schema_hint="risks array with risk, severity, reason, source_section")

    risks = []
    for item in to_list(data.get("risks")):
        risks.append({
            "risk": get_str(item.get("risk")),
            "severity": get_str(item.get("severity")),
            "reason": get_str(item.get("reason")),
            "source_section": get_str(item.get("source_section"))
        })

    return {
        "risks": risks,
        "reasoning": [get_str(r) for r in to_list(data.get("reasoning"))]
    }
