from services.ai_json import parse_json_with_retry, to_list, get_str


def run_notification_agent(context: str) -> dict:
    prompt = (
        "You are a notification agent. Return ONLY valid JSON. "
        "Schema: {\"alerts\":[\"...\"],\"reasoning\":[\"...\"]}. "
        "Create concise compliance alerts for leaders.\nContext:\n" + context
    )
    data = parse_json_with_retry(prompt, schema_hint="alerts list and reasoning list")

    return {
        "alerts": [get_str(a) for a in to_list(data.get("alerts"))],
        "reasoning": [get_str(r) for r in to_list(data.get("reasoning"))]
    }
