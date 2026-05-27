import re
from services.ai_json import parse_json_with_retry, to_list, get_str
from services.prompt_templates import SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE

# Phase 6: Enhanced Department mapping for Indian banking compliance orgs
DEPARTMENT_ALIASES = {
    "compliance": "Compliance",
    "risk": "Risk Management",
    "audit": "Internal Audit",
    "it": "IT & Cybersecurity",
    "technology": "IT & Cybersecurity",
    "cyber": "IT & Cybersecurity",
    "operations": "Operations",
    "legal": "Legal",
    "treasury": "Treasury",
    "hr": "Human Resources",
    "finance": "Finance",
    "aml": "AML Operations",
    "financial crime": "AML Operations",
    "vendor": "Third-Party Risk",
    "outsourcing": "Third-Party Risk",
    "third-party": "Third-Party Risk",
    "third party": "Third-Party Risk",
    "board": "Board & Governance",
    "governance": "Board & Governance",
}

# Phase 6: Fine-grained keyword-to-department routing
_DEPT_KEYWORD_RULES = [
    # KYC/CDD -> Compliance (must come BEFORE generic "it" match)
    (["kyc", "know your customer", "cdd", "customer due diligence", "v-cip", "vcip",
      "onboarding", "identity verification", "customer identification"], "Compliance"),
    # AML/CFT -> AML Operations
    (["aml", "anti-money laundering", "money laundering", "fiu-ind", "fiu",
      "suspicious transaction", "str", "ctr", "cash transaction report",
      "terror financing", "uapa", "pmla", "financial crime"], "AML Operations"),
    # Vendor/Third-party -> Third-Party Risk
    (["vendor", "outsourcing", "third-party", "third party", "supplier",
      "sla", "service level agreement", "procurement"], "Third-Party Risk"),
    # Cyber/IT -> IT & Cybersecurity
    (["cyber", "security", "firewall", "mfa", "multi-factor", "encryption",
      "vapt", "penetration testing", "ddos", "tls", "token", "password",
      "network", "access control", "incident response"], "IT & Cybersecurity"),
    # Audit -> Internal Audit
    (["audit", "inspection", "verification", "log review", "testing"], "Internal Audit"),
    # Board/Governance
    (["board", "director", "ciso", "committee", "governance", "management"], "Board & Governance"),
    # Legal
    (["legal", "law", "penalty", "fine", "prosecution", "sanction", "act"], "Legal"),
    # Operations
    (["ops", "operation", "transaction", "process", "settlement", "clearing",
      "reconciliation", "day-to-day"], "Operations"),
    # HR
    (["hr", "training", "employee", "staff", "awareness"], "Human Resources"),
]


def _normalize_department(raw: str) -> str:
    """Phase 6: Enhanced department classification with keyword priority rules."""
    if not raw or not raw.strip():
        return "Compliance"
    key = raw.strip().lower()

    # First try fine-grained keyword matching (order matters - KYC before IT)
    for keywords, dept in _DEPT_KEYWORD_RULES:
        if any(kw in key for kw in keywords):
            return dept

    # Then try alias matching
    for alias, canonical in DEPARTMENT_ALIASES.items():
        if alias in key:
            return canonical

    return raw.strip().title()


def _extract_deadline_days(deadline: str):
    """Parse '45 days', 'within 30 days', '6 months' into approximate day count."""
    if not deadline:
        return None
    m = re.search(r"(\d+)\s*(day|days|month|months|week|weeks)", deadline.lower())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    if "month" in unit:
        return n * 30
    if "week" in unit:
        return n * 7
    return n


def _confidence_score(item: dict) -> float:
    """Heuristic confidence based on field completeness and source citation."""
    score = 0.4
    if get_str(item.get("title")):
        score += 0.2
    if get_str(item.get("source_section")):
        score += 0.25
    if get_str(item.get("deadline")):
        score += 0.1
    if get_str(item.get("department")):
        score += 0.05
    return round(min(1.0, score), 2)


def run_compliance_agent(context: str) -> dict:
    prompt = (
        SYSTEM_PROMPT + "\n" +
        "You are focusing on COMPLIANCE — extract Measurable Action Points (MAPs).\n"
        "Return ONLY valid JSON:\n"
        '{"maps":[{"title","department","deadline","severity","source_section","confidence"}],'
        '"reasoning":["..."]}\n'
        "- deadline: explicit timeline from document (e.g. 'within 45 days')\n"
        "- confidence: 0.0-1.0 how certain you are this MAP is grounded in context\n"
        "- department: map to Compliance, Risk Management, IT & Cybersecurity, Operations, Legal, Internal Audit\n\n"
        + ANALYSIS_PROMPT_TEMPLATE.format(context=context)
    )
    data = parse_json_with_retry(
        prompt,
        schema_hint="maps with title, department, deadline, severity, source_section, confidence",
    )

    maps = []
    for item in to_list(data.get("maps")):
        deadline = get_str(item.get("deadline"))
        dept = _normalize_department(get_str(item.get("department")))
        conf = item.get("confidence")
        if not isinstance(conf, (int, float)):
            conf = _confidence_score(item)
        maps.append({
            "title": get_str(item.get("title")),
            "department": dept,
            "deadline": deadline,
            "deadline_days": _extract_deadline_days(deadline),
            "severity": get_str(item.get("severity"), "Medium"),
            "source_section": get_str(item.get("source_section")),
            "confidence": float(conf),
        })

    return {
        "maps": maps,
        "reasoning": [get_str(r) for r in to_list(data.get("reasoning"))]
    }
