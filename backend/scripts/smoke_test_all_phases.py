"""API smoke test for all MASTER_PLAN_2 phases."""
import json
import requests

BASE = "http://127.0.0.1:8000/api"

def main():
    r = requests.post(
        f"{BASE}/auth/token",
        data={"username": "admin", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    results = {}

    def check(name, method, path, **kw):
        try:
            resp = getattr(requests, method)(f"{BASE}{path}", headers=h, timeout=120, **kw)
            results[name] = {"ok": resp.status_code < 400, "status": resp.status_code}
            return resp
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)}
            return None

    check("Phase5 Dashboard", "get", "/dashboard")
    check("Phase5 Analytics", "get", "/analytics")
    check("Phase7 Corpus sources", "get", "/corpus/sources")
    check("Phase7 Corpus stats", "get", "/corpus/stats")
    check("Phase8 Scrape status", "get", "/scrape/status")
    check("Phase12 CSV report", "get", "/reports/compliance")
    check("Phase12 PDF report", "get", "/reports/executive-pdf")
    check("Phase12 DOCX report", "get", "/reports/board-docx")
    check("Phase14 Metrics", "get", "/observability/metrics")
    check("Phase14 Traces", "get", "/observability/traces?limit=5")

    # Upload test PDF
    import os
    pdf = os.path.join(os.path.dirname(__file__), "..", "test_pdfs", "RBI_KYC_Test.pdf")
    if os.path.exists(pdf):
        with open(pdf, "rb") as f:
            up = requests.post(
                f"{BASE}/upload-document",
                files={"file": ("RBI_KYC_Test.pdf", f, "application/pdf")},
                headers=h,
                timeout=120,
            )
        results["Phase1-2 Upload"] = {"ok": up.status_code == 200, "status": up.status_code}
        if up.status_code == 200:
            doc_id = up.json()["document_id"]
            an = requests.post(f"{BASE}/analyze-document", params={"doc_id": doc_id}, headers=h, timeout=300)
            results["Phase3-4 Analyze"] = {"ok": an.status_code == 200, "status": an.status_code}
            if an.status_code == 200:
                g = requests.get(f"{BASE}/knowledge-graph/{doc_id}", headers=h, timeout=120)
                results["Phase10 Graph"] = {"ok": g.status_code == 200, "nodes": len(g.json().get("nodes", []))}
                c = requests.post(f"{BASE}/chat", json={"document_id": doc_id, "message": "What are KYC deadlines?"}, headers=h, timeout=120)
                results["Phase11 Chat"] = {"ok": c.status_code == 200, "grounded": c.json().get("grounded")}

    passed = sum(1 for v in results.values() if v.get("ok"))
    print(json.dumps(results, indent=2))
    print(f"\nAPI SMOKE: {passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
