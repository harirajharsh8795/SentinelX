from services.ai_json import parse_json_with_retry, to_list, get_str


def run_audit_agent(context: str) -> dict:
    prompt = (
        "You are an audit agent. Return ONLY valid JSON. "
        "Schema: {\"audit\":[\"...\"],\"reasoning\":[\"...\"]}. "
        "Create short audit trail notes for the analysis.\nContext:\n" + context
    )
    data = parse_json_with_retry(prompt, schema_hint="audit list and reasoning list")

    return {
        "audit": [get_str(a) for a in to_list(data.get("audit"))],
        "reasoning": [get_str(r) for r in to_list(data.get("reasoning"))]
    }
