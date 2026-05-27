"""
Phase 7 — Master Regulatory Corpus Registry
Defines RBI, SEBI, CERT-IN, NPCI, SWIFT, and ISO framework sources.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CorpusSourceDef:
    code: str
    name: str
    framework: str
    description: str
    base_url: Optional[str]
    corpus_subdir: str
    seed_filename: str


REGULATORY_SOURCES: List[CorpusSourceDef] = [
    CorpusSourceDef(
        code="RBI",
        name="Reserve Bank of India",
        framework="Banking Regulation & KYC/AML",
        description="RBI Master Directions, circulars on KYC, AML/CFT, digital lending, and payment systems.",
        base_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx",
        corpus_subdir="RBI",
        seed_filename="rbi_kyc_master_direction.txt",
    ),
    CorpusSourceDef(
        code="SEBI",
        name="Securities and Exchange Board of India",
        framework="Market Regulation & LODR",
        description="SEBI LODR, insider trading, cybersecurity for MIIs, and disclosure norms.",
        base_url="https://www.sebi.gov.in/legal/circulars.html",
        corpus_subdir="SEBI",
        seed_filename="sebi_lodr_cybersecurity.txt",
    ),
    CorpusSourceDef(
        code="CERTIN",
        name="Indian Computer Emergency Response Team",
        framework="Cyber Security & Incident Response",
        description="CERT-In directions on log retention, incident reporting timelines, and SOC requirements.",
        base_url="https://www.cert-in.org.in/",
        corpus_subdir="CERTIN",
        seed_filename="certin_incident_reporting.txt",
    ),
    CorpusSourceDef(
        code="NPCI",
        name="National Payments Corporation of India",
        framework="UPI / IMPS / Payment Systems",
        description="NPCI operating guidelines for UPI, dispute resolution, and participant compliance.",
        base_url="https://www.npci.org.in/",
        corpus_subdir="NPCI",
        seed_filename="npci_upi_operating_guidelines.txt",
    ),
    CorpusSourceDef(
        code="SWIFT",
        name="SWIFT Customer Security Programme",
        framework="CSP & Financial Messaging Security",
        description="SWIFT CSP mandatory controls, attestation, and fraud prevention for cross-border payments.",
        base_url="https://www.swift.com/myswift/customer-security-programme-csp",
        corpus_subdir="SWIFT",
        seed_filename="swift_csp_controls.txt",
    ),
    CorpusSourceDef(
        code="ISO27001",
        name="ISO/IEC 27001 Information Security",
        framework="ISMS & Annex A Controls",
        description="ISO 27001 ISMS requirements and Annex A control objectives for banking IT.",
        base_url="https://www.iso.org/standard/54534.html",
        corpus_subdir="ISO",
        seed_filename="iso27001_annex_a_summary.txt",
    ),
]


def get_source_by_code(code: str) -> Optional[CorpusSourceDef]:
    return next((s for s in REGULATORY_SOURCES if s.code.upper() == code.upper()), None)


def all_source_codes() -> List[str]:
    return [s.code for s in REGULATORY_SOURCES]
