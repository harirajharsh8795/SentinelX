"""
Phase 12 — Report Generation: CSV, PDF executive summary, DOCX board report.
"""
import io
import csv
from datetime import datetime, timezone
from typing import List
from database.database import SessionLocal
from database.models import Task, Alert, Document


def _fetch_report_data(document_id: str = None):
    db = SessionLocal()
    from services.log_service import _resolve_document_id
    doc_id = _resolve_document_id(db, document_id)
    tasks = db.query(Task).filter(Task.document_id == doc_id).all()
    alerts = db.query(Alert).filter(Alert.document_id == doc_id).all()
    documents = db.query(Document).filter(Document.id == doc_id).all()
    db.close()
    return tasks, alerts, documents


def generate_compliance_report_csv(document_id: str = None) -> str:
    tasks, alerts, documents = _fetch_report_data(document_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["--- COMPLIANCE SYSTEM REPORT ---"])
    writer.writerow(["Generated", datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M UTC")])
    writer.writerow(["Total Documents Indexed", len(documents)])
    writer.writerow(["Active Alerts", len(alerts)])
    writer.writerow(["Total Tasks", len(tasks)])
    writer.writerow([""])
    writer.writerow(["--- OPEN COMPLIANCE TASKS ---"])
    writer.writerow(["Task ID", "Title", "Department", "Priority", "Status", "Deadline"])
    for t in tasks:
        writer.writerow([t.id, t.title, t.department, t.priority, t.status, t.deadline])
    writer.writerow([""])
    writer.writerow(["--- RISK ALERTS ---"])
    writer.writerow(["Alert ID", "Title", "Severity", "Created At"])
    for a in alerts:
        writer.writerow([a.id, a.title, a.severity, a.created_at])
    return output.getvalue()


def generate_executive_pdf(document_id: str = None) -> bytes:
    """Board-ready PDF summary using fpdf2."""
    from fpdf import FPDF

    tasks, alerts, documents = _fetch_report_data(document_id)
    high_priority = [t for t in tasks if (t.priority or "").lower() == "high" and (t.status or "").lower() == "pending"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    w = pdf.epw

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(w, 10, "SentinelX - Executive Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(w, 8, f"Generated: {datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M UTC')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(w, 8, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    summary = (
        f"Documents: {len(documents)} | Alerts: {len(alerts)} | "
        f"Tasks: {len(tasks)} | High-priority pending: {len(high_priority)}"
    )
    pdf.multi_cell(w, 6, summary)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(w, 8, "High-Priority Actions", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    if high_priority:
        for t in high_priority[:15]:
            line = f"- {(t.department or 'General')[:20]}: {(t.title or 'Task')[:60]}"
            pdf.multi_cell(w, 5, line.encode("latin-1", "replace").decode("latin-1"))
    else:
        pdf.multi_cell(w, 5, "No high-priority pending tasks.")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(w, 8, "Active Risk Alerts", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for a in alerts[:10]:
        line = f"- [{(a.severity or 'medium')[:8]}] {(a.title or 'Alert')[:70]}"
        pdf.multi_cell(w, 5, line.encode("latin-1", "replace").decode("latin-1"))

    return bytes(pdf.output())


def generate_board_docx(document_id: str = None) -> bytes:
    """Board summary DOCX using python-docx."""
    from docx import Document as DocxDocument
    from docx.shared import Pt, Inches

    tasks, alerts, documents = _fetch_report_data(document_id)
    doc = DocxDocument()
    doc.add_heading("SentinelX — Board Compliance Summary", 0)
    doc.add_paragraph(f"Report Date: {datetime.now(timezone.utc).replace(tzinfo=None).strftime('%d %B %Y')}")
    doc.add_heading("Executive Overview", level=1)
    doc.add_paragraph(
        f"The compliance intelligence platform currently monitors {len(documents)} regulatory "
        f"documents with {len(tasks)} tracked action items and {len(alerts)} active alerts."
    )
    doc.add_heading("Priority Compliance Actions", level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "Department"
    hdr[1].text = "Action"
    hdr[2].text = "Priority"
    hdr[3].text = "Deadline"
    for t in tasks[:20]:
        row = table.add_row().cells
        row[0].text = t.department or "General"
        row[1].text = t.title or ""
        row[2].text = t.priority or ""
        row[3].text = t.deadline or ""
    doc.add_heading("Risk Alerts", level=1)
    for a in alerts[:10]:
        doc.add_paragraph(f"{a.title} — Severity: {a.severity}", style="List Bullet")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
