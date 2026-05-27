from services.ai_json import parse_json_with_retry, to_list, get_str


def run_executive_agent(context: str) -> dict:
    prompt = (
        "You are an executive compliance advisor. Return ONLY valid JSON. "
        "Schema: {\"executive_insights\":\"...\",\"reasoning\":[\"...\"]}. "
        "Summarize business impact, exposure, and recommended next actions.\n"
        "Context:\n" + context
    )
    data = parse_json_with_retry(prompt, schema_hint="executive_insights string and reasoning list")

    return {
        "executive_insights": get_str(data.get("executive_insights")),
        "reasoning": [get_str(r) for r in to_list(data.get("reasoning"))]
    }
