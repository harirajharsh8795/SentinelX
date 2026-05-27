"""Create valid test PDFs for batch testing."""
import os
from fpdf import FPDF

OUT = os.path.join(os.path.dirname(__file__), "..", "test_pdfs")
os.makedirs(OUT, exist_ok=True)

SAMPLES = {
    "RBI_KYC_Test.pdf": [
        "RBI Master Direction on KYC",
        "Section 1: All banks must complete KYC refresh within 45 days for high-risk customers.",
        "Section 2: STR filing required within 7 days of suspicious activity detection.",
        "Penalty: Non-compliance may attract monetary penalty under PMLA Section 13.",
    ],
    "SEBI_Cyber_Test.pdf": [
        "SEBI Cybersecurity Framework for MIIs",
        "Regulation 47: Annual VAPT mandatory. Incident reporting within 6 hours.",
        "Board must approve Cyber Crisis Management Plan annually.",
    ],
    "CERTIN_Incident_Test.pdf": [
        "CERT-In Directions Section 70B",
        "Incident reporting within 6 hours to CERT-In portal.",
        "Log retention 180 days within Indian jurisdiction.",
    ],
}

for filename, lines in SAMPLES.items():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    w = pdf.epw
    for line in lines:
        pdf.multi_cell(w, 7, line)
        pdf.ln(2)
    path = os.path.join(OUT, filename)
    pdf.output(path)
    print("Created", path)

print(f"Done — {len(SAMPLES)} PDFs in {OUT}")
