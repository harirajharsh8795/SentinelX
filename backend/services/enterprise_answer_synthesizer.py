"""
Phase 3 — Enterprise Synthesis Engine
Merges retrieved chunks, deduplicates context, and synthesizes agent outputs
into executive-ready intelligence.
"""
from typing import Any, Dict, List
import hashlib

from services.gemini_service import generate_text
from services.ai_json import parse_json_with_retry, get_str, to_list
from utils.input_sanitizer import sanitize_document_text  # Security: Prompt injection defense


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


def generate_fallback_executive_intelligence(maps: List[dict], risks: List[dict], context: str) -> dict:
    """
    Resilient, deterministic fallback generator producing the 11-section executive compliance structure.
    """
    import re
    regulator = "SEBI" if "sebi" in context.lower() else "RBI"
    circ_match = re.search(r'circular no\.?\s*([A-Za-z0-9\-/_]+)', context, re.IGNORECASE)
    circ_num = circ_match.group(1) if circ_match else f"{regulator}_CIRCULAR_REGISTRY"
    
    rating = "SATISFACTORY"
    if risks:
        if any(r.get("severity", "Medium").lower() == "high" for r in risks):
            rating = "CRITICAL RISK"
        else:
            rating = "NEEDS IMMEDIATE ACTION"
            
    findings = []
    for r in risks[:3]:
        findings.append({
            "finding": r.get("risk", "Compliance Vulnerability"),
            "impact": r.get("reason", "Lapse in governance oversight controls."),
            "severity": r.get("severity", "Medium"),
            "remediation": f"Implement controls as defined in section {r.get('source_section', 'General')}."
        })
    if not findings:
        findings.append({
            "finding": "Standard Regulatory Alignment Review Required",
            "impact": "Verification of compliance registry is pending.",
            "severity": "Medium",
            "remediation": "Perform gap analysis against circular guidelines."
        })
        
    obligations = []
    for m in maps[:4]:
        obligations.append({
            "obligation": m.get("title", "Review guidelines"),
            "department": m.get("department", "Compliance"),
            "deadline": m.get("deadline", "90 Days"),
            "priority": m.get("severity", "Medium"),
            "source_section": m.get("source_section", "General")
        })
    if not obligations:
        obligations.append({
            "obligation": "Review circular guidelines and perform gap analysis",
            "department": "Compliance",
            "deadline": "30 Days",
            "priority": "Medium",
            "source_section": "General"
        })
        
    board = []
    ops = []
    for m in maps:
        title = m.get("title", "")
        dept = m.get("department", "Compliance")
        if dept in ["Compliance", "Legal"] or "board" in title.lower() or "policy" in title.lower() or "governance" in title.lower():
            board.append({
                "responsibility": f"Oversight and approval for compliance implementation: {title}",
                "focus": "Governance & Regulatory Policy Framework",
                "committee": "Audit Committee" if "audit" in title.lower() else "Risk Management Committee",
                "milestone": "Approval of Framework Updates"
            })
        else:
            ops.append({
                "action": f"Deploy system updates and training schedules for: {title}",
                "department": dept,
                "parameter": "Process integration & validation",
                "verification": "System testing and audit trails sign-off"
            })
            
    if not board:
        board = [
            {
                "responsibility": "Establish oversight committee to monitor circular compliance updates",
                "focus": "Regulatory Compliance Oversight",
                "committee": "Risk Management Committee",
                "milestone": "Committee Charter Approval"
            },
            {
                "responsibility": "Approve compliance framework adjustment for SentinelX",
                "focus": "Board Governance Policy",
                "committee": "Board of Directors",
                "milestone": "Board Resolution Approved"
            }
        ]
    if not ops:
        ops = [
            {
                "action": "Perform operational system updates to align with parameters",
                "department": "IT & Cybersecurity",
                "parameter": "Security patch deployment",
                "verification": "System scans and vulnerability testing"
            },
            {
                "action": "Assign departmental owners for compliance tasks",
                "department": "Compliance",
                "parameter": "Workflow assignment",
                "verification": "Task assignment log validated"
            }
        ]
        
    heatmap = []
    for r in risks[:5]:
        severity = r.get("severity", "Medium").lower()
        l = 2
        imp = 2
        if severity == "high":
            l = 4
            imp = 4
        elif severity == "medium":
            l = 3
            imp = 3
        heatmap.append({
            "risk": r.get("risk", "Vulnerability"),
            "likelihood": l,
            "impact": imp,
            "category": "Technology" if "cyber" in r.get("risk", "").lower() or "it" in r.get("risk", "").lower() else "Governance"
        })
    if not heatmap:
        heatmap.append({
            "risk": "Regulatory non-alignment",
            "likelihood": 2,
            "impact": 3,
            "category": "Regulatory"
        })
        
    roadmap = [
        {
            "phase": "Immediate (0-30 Days)",
            "actions": [
                {
                    "action": m.get("title") or "Setup compliance review project team",
                    "owner": m.get("department") or "Compliance",
                    "priority": "High"
                } for m in maps[:2]
            ] if maps else [
                {
                    "action": "Setup compliance review project team",
                    "owner": "Compliance",
                    "priority": "High"
                }
            ]
        },
        {
            "phase": "Short-Term (30-90 Days)",
            "actions": [
                {
                    "action": m.get("title") or "Implement core control framework revisions",
                    "owner": m.get("department") or "Operations",
                    "priority": "Medium"
                } for m in maps[2:4]
            ] if len(maps) > 2 else [
                {
                    "action": "Implement core control framework revisions",
                    "owner": "Operations",
                    "priority": "Medium"
                }
            ]
        },
        {
            "phase": "Medium-Term (90+ Days)",
            "actions": [
                {
                    "action": m.get("title") or "Review compliance alignment reports",
                    "owner": m.get("department") or "Internal Audit",
                    "priority": "Low"
                } for m in maps[4:6]
            ] if len(maps) > 4 else [
                {
                    "action": "Review compliance alignment reports",
                    "owner": "Internal Audit",
                    "priority": "Low"
                }
            ]
        }
    ]
    
    score = 100
    deductions = []
    if risks:
        high_cnt = sum(1 for r in risks if r.get("severity", "Medium").lower() == "high")
        med_cnt = sum(1 for r in risks if r.get("severity", "Medium").lower() == "medium")
        score = max(10, 100 - (high_cnt * 15) - (med_cnt * 5))
        if high_cnt > 0:
            deductions.append({
                "finding": f"Detection of {high_cnt} High-severity regulatory findings",
                "points": high_cnt * 15
            })
        if med_cnt > 0:
            deductions.append({
                "finding": f"Detection of {med_cnt} Medium-severity compliance vulnerabilities",
                "points": med_cnt * 5
            })
            
    recs = []
    for r in risks[:3]:
        recs.append({
            "recommendation": f"Establish program to address {r.get('risk')}: {r.get('mitigation')}",
            "priority_label": "Immediate Priority" if r.get("severity", "Medium").lower() == "high" else "Strategic Move",
            "difficulty": "Medium",
            "payoff": "High"
        })
    if not recs:
        recs.append({
            "recommendation": "Conduct full internal audit of operational controls",
            "priority_label": "Strategic Move",
            "difficulty": "Medium",
            "payoff": "High"
        })
        
    citations = []
    for r in risks[:3]:
        citations.append({
            "citation": r.get("source_section") or "Relevant Circular Clause",
            "text": r.get("reason", "Regulatory mandate"),
            "relevance": "High"
        })
    if not citations:
        citations.append({
            "citation": "Retrieved circular text context",
            "text": "General regulatory expectations",
            "relevance": "Medium"
        })
        
    return {
        "executive_summary": {
            "regulator": regulator,
            "circular_reference": circ_num,
            "effective_date": "Immediate" if "immediate" in context.lower() else "Within 90 Days",
            "overview": f"This regulatory brief details the compliance alignment path under the {regulator} framework for circular {circ_num}.",
            "key_metrics": [
                {
                    "metric": "Active Risks Detected",
                    "value": str(len(risks)),
                    "context": "Identified threat vectors"
                },
                {
                    "metric": "Assigned Directives",
                    "value": str(len(maps)),
                    "context": "Assigned operational MAP items"
                },
                {
                    "metric": "Critical Due Date",
                    "value": "Immediate" if any(r.get("severity", "Medium").lower() == "high" for r in risks) else "90 Days",
                    "context": "Regulatory compliance timeline"
                }
            ]
        },
        "compliance_posture": {
            "rating": rating,
            "readiness_score": f"{score}%",
            "exposure_level": "High" if rating == "CRITICAL RISK" else "Medium",
            "governance_health": "Deficient" if rating == "CRITICAL RISK" else "Needs Restructuring",
            "assessment_bullets": [
                f"Identified {len(risks)} compliance risks across the operational systems.",
                f"Required audit reviews established for departments: {', '.join(list({m.get('department') for m in maps if m.get('department')})) or 'Compliance'}."
            ]
        },
        "critical_findings": findings,
        "regulatory_obligations": obligations,
        "board_responsibilities": board[:4],
        "operational_responsibilities": ops[:4],
        "risk_heatmap": heatmap,
        "remediation_roadmap": roadmap,
        "compliance_score": {
            "score": score,
            "deductions": deductions,
            "rationale": f"Scoring is adjusted to {score}% due to detection of {len(risks)} risks requiring operational oversight."
        },
        "strategic_recommendations": recs,
        "source_citations": citations
    }


def synthesize_executive_summary(
    maps: List[dict],
    risks: List[dict],
    context_preview: str,
) -> Dict[str, Any]:
    """
    Phase 7: Generate rich executive compliance intelligence structure matching McKinsey and Deloitte briefs.
    """
    maps_summary = "\n".join(
        f"- {m.get('title', 'N/A')} [{m.get('department', 'General')}] "
        f"deadline={m.get('deadline', 'N/A')} severity={m.get('severity', 'Medium')} source={m.get('source_section', 'N/A')}"
        for m in maps[:12]
    ) or "No MAPs extracted."
    risks_summary = "\n".join(
        f"- {r.get('risk', 'N/A')} [{r.get('severity', 'Low')}] mitigation={r.get('mitigation', 'N/A')} source={r.get('source_section', 'N/A')}"
        for r in risks[:12]
    ) or "No risks identified."

    prompt = f"""You are a McKinsey Partner, Deloitte Compliance Advisor, and Executive Intelligence Architect.
Based on the extracted compliance MAPs and risks below, generate a comprehensive compliance brief for SentinelX.

Every section must be fully grounded in the document context. Return ONLY a valid JSON object matching this schema:
{{
  "executive_summary": {{
    "regulator": "SEBI or RBI",
    "circular_reference": "circular identification reference string",
    "effective_date": "effective date of circular",
    "overview": "McKinsey-style executive oversight summary",
    "key_metrics": [
      {{
        "metric": "Label of key metric",
        "value": "Value of key metric (e.g. 5, 30 Days, Critical, etc.)",
        "context": "Context description of what this metric represents"
      }}
    ]
  }},
  "compliance_posture": {{
    "rating": "CRITICAL RISK | NEEDS IMMEDIATE ACTION | SATISFACTORY",
    "readiness_score": "Score value (e.g. 70%)",
    "exposure_level": "High | Medium | Low",
    "governance_health": "Deficient | Needs Restructuring | Resilient",
    "assessment_bullets": [
      "Detail 1 regarding systemic exposure or readiness gaps",
      "Detail 2 regarding controls check and operational alignment"
    ]
  }},
  "critical_findings": [
    {{
      "finding": "Short description of key regulatory finding",
      "impact": "Business, financial, or operational impact",
      "severity": "High | Medium | Low",
      "remediation": "Brief description of the proposed operational remediation"
    }}
  ],
  "regulatory_obligations": [
    {{
      "obligation": "Clear statement of obligation",
      "department": "Department owner (e.g. IT & Cybersecurity, Operations, AML Operations, etc.)",
      "deadline": "Deadline timeline",
      "priority": "High | Medium | Low",
      "source_section": "Section or clause number"
    }}
  ],
  "board_responsibilities": [
    {{
      "responsibility": "Board action/policy approval duty",
      "focus": "Governance or policy focus",
      "committee": "Audit Committee | Risk Management Committee | IT Strategy Committee | Board of Directors",
      "milestone": "timeline or resolution milestone"
    }}
  ],
  "operational_responsibilities": [
    {{
      "action": "Operational task item or deployment step",
      "department": "Target Department (e.g. Compliance, Operations, IT, etc.)",
      "parameter": "deployment or workflow parameter details",
      "verification": "verification or audit validation check"
    }}
  ],
  "risk_heatmap": [
    {{
      "risk": "Name of threat",
      "likelihood": 1 to 5 index,
      "impact": 1 to 5 index,
      "category": "Technology | Process | Governance | Regulatory"
    }}
  ],
  "remediation_roadmap": [
    {{
      "phase": "Immediate (0-30 Days)",
      "actions": [
        {{
          "action": "roadmap item action text",
          "owner": "Department owner",
          "priority": "High | Medium | Low"
        }}
      ]
    }},
    {{
      "phase": "Short-Term (30-90 Days)",
      "actions": [
        {{
          "action": "roadmap item action text",
          "owner": "Department owner",
          "priority": "High | Medium | Low"
        }}
      ]
    }},
    {{
      "phase": "Medium-Term (90+ Days)",
      "actions": [
        {{
          "action": "roadmap item action text",
          "owner": "Department owner",
          "priority": "High | Medium | Low"
        }}
      ]
    }}
  ],
  "compliance_score": {{
    "score": 0 to 100 value,
    "deductions": [
      {{
        "finding": "Short reason for score deduction based on finding",
        "points": score deduction amount (e.g. 15 for high risk, 5 for medium)
      }}
    ],
    "rationale": "Detailed rationale for this score based on severity of findings"
  }},
  "strategic_recommendations": [
    {{
      "recommendation": "Strategic Deloitte/McKinsey-style recommendation",
      "priority_label": "Immediate Priority | Strategic Move | Operational Control",
      "difficulty": "High | Medium | Low",
      "payoff": "High | Medium | Low"
    }}
  ],
  "source_citations": [
    {{
      "citation": "circular reference section or clause name",
      "text": "verbatim text segment from document context backing this citation",
      "relevance": "High | Medium | Low"
    }}
  ]
}}

Format requirements:
- Use clear, action-oriented, precise language (no placeholders).
- Do not repeat text across different keys.
- Ensure Likelihood and Impact are integers between 1 and 5.
- Fill all fields completely.

--- MAPs ---
{maps_summary}

--- RISKS ---
{risks_summary}

--- DOCUMENT CONTEXT ---
{sanitize_document_text(context_preview[:3000], max_chars=3000, source_label="synthesis_context")}
"""
    try:
        data = parse_json_with_retry(
            prompt,
            schema_hint="executive_summary, compliance_posture, critical_findings, regulatory_obligations, board_responsibilities, operational_responsibilities, risk_heatmap, remediation_roadmap, compliance_score, strategic_recommendations, source_citations"
        )
        required_keys = [
            "executive_summary", "compliance_posture", "critical_findings", 
            "regulatory_obligations", "board_responsibilities", "operational_responsibilities", 
            "risk_heatmap", "remediation_roadmap", "compliance_score", 
            "strategic_recommendations", "source_citations"
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")
        return data
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Structured synthesis failed: {exc}. Generating comprehensive fallback.")
        return generate_fallback_executive_intelligence(maps, risks, context_preview)


def enrich_agent_output(agent_output: dict, context: str) -> dict:
    """
    Full synthesis pipeline: enrich raw agent outputs with executive intelligence.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Ensure agent_output has maps if risks exist to guarantee the Risk -> MAP flow
    maps = list(agent_output.get("maps", []))
    risks = agent_output.get("risks", [])
    if risks:
        for r in risks:
            risk_title = r.get("risk", "")
            source_sec = r.get("source_section", "")
            severity = r.get("severity", "Medium")
            mitigation = r.get("mitigation", "")
            
            has_match = False
            for m in maps:
                m_sec = m.get("source_section", "") or ""
                m_title = m.get("title", "") or ""
                if source_sec and m_sec and (source_sec.lower() in m_sec.lower() or m_sec.lower() in source_sec.lower()):
                    has_match = True
                    break
                if risk_title and m_title and (risk_title.lower() in m_title.lower() or m_title.lower() in risk_title.lower()):
                    has_match = True
                    break
                    
            if not has_match:
                # Auto-generate directive title directly from risk title and mitigation
                r_lower = risk_title.lower()
                if r_lower.startswith("missing "):
                    directive_title = f"Implement board-approved {risk_title[8:]}"
                elif "lack of " in r_lower:
                    idx = r_lower.find("lack of ")
                    directive_title = f"Establish structured {risk_title[idx+8:]}"
                elif r_lower.startswith("absence of "):
                    directive_title = f"Deploy required {risk_title[11:]}"
                elif "failure to " in r_lower:
                    idx = r_lower.find("failure to ")
                    directive_title = f"Ensure compliance with requirement to {risk_title[idx+11:]}"
                elif "non-compliance with " in r_lower:
                    idx = r_lower.find("non-compliance with ")
                    directive_title = f"Align controls with {risk_title[idx+20:]}"
                else:
                    if mitigation and len(mitigation) < 80:
                        directive_title = mitigation
                    else:
                        directive_title = f"Remediate {risk_title}"
                
                # Classify department owner based on risk keywords
                dept = "Compliance"
                if any(w in r_lower for w in ["mfa", "cyber", "access", "technical", "encryption", "tls", "security", "it ", "system", "infrastructure"]):
                    dept = "IT & Cybersecurity"
                elif any(w in r_lower for w in ["audit", "inspection", "verify", "reconcile", "reconciliation"]):
                    dept = "Internal Audit"
                elif any(w in r_lower for w in ["aml", "money laundering", "str", "kyc", "customer identity"]):
                    dept = "AML Operations"
                elif any(w in r_lower for w in ["transaction", "deposit", "payment", "limit", "operations"]):
                    dept = "Operations"
                    
                deadline = "90 Days"
                if severity.lower() == "high":
                    deadline = "Immediate"
                elif severity.lower() == "medium":
                    deadline = "30 Days"
                    
                citation = source_sec if source_sec else ("Relevant SEBI Clause" if "sebi" in context.lower() else "Relevant RBI Clause")
                
                maps.append({
                    "title": directive_title[:200],
                    "department": dept,
                    "deadline": deadline,
                    "severity": severity,
                    "source_section": citation
                })
        agent_output["maps"] = maps

    try:
        synthesis = synthesize_executive_summary(
            agent_output.get("maps", []),
            agent_output.get("risks", []),
            context[:3000],
        )
    except Exception as exc:
        logger.error(f"Executive synthesis failed: {exc}. Generating fallback synthesis.")
        synthesis = generate_fallback_executive_intelligence(
            agent_output.get("maps", []),
            agent_output.get("risks", []),
            context[:3000]
        )

    import json
    # Serialize the complete 11-section brief into executive_insights
    executive_text = json.dumps(synthesis)

    reasoning = list(agent_output.get("agent_reasoning", []))
    reasoning.append("Executive Synthesis: Generated 11-section McKinsey/Deloitte compliance brief.")

    # Preserve and deduplicate mitigations for risks
    enriched_risks = list(agent_output.get("risks", []))
    seen_mitigations = set()
    for i, r in enumerate(enriched_risks):
        mit = r.get("mitigation", "").strip()
        if not mit or mit in seen_mitigations:
            dept = "Compliance"
            risk_lower = r.get("risk", "").lower()
            if any(w in risk_lower for w in ["mfa", "cyber", "access", "technical", "encryption", "tls", "security"]):
                dept = "IT & Cybersecurity"
            elif any(w in risk_lower for w in ["audit", "inspection", "verify"]):
                dept = "Internal Audit"
            elif any(w in risk_lower for w in ["aml", "money laundering", "str"]):
                dept = "AML Operations"
            r["mitigation"] = f"Establish specific oversight controls to mitigate {r.get('risk')} under the {dept} department."
            
            if r["mitigation"] in seen_mitigations:
                r["mitigation"] = f"Establish specific oversight controls to mitigate {r.get('risk')} under the {dept} department (Ref: Control-{i+1})."
        seen_mitigations.add(r["mitigation"])

    return {
        **agent_output,
        "executive_insights": executive_text,
        "risks": enriched_risks,
        "agent_reasoning": reasoning,
        "synthesis": synthesis,
    }
