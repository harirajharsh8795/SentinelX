"""Batch test all PDFs in cloud_storage_mock/sentinel-documents."""
import os
import sys
import json
import requests

BASE = "http://127.0.0.1:8000/api"
PDF_DIR = os.environ.get(
    "TEST_PDF_DIR",
    os.path.join(os.path.dirname(__file__), "..", "test_pdfs"),
)


def login():
    r = requests.post(
        f"{BASE}/auth/token",
        data={"username": "admin", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def run_pdf_test(path: str, token: str) -> dict:
    name = os.path.basename(path)
    headers = {"Authorization": f"Bearer {token}"}
    result = {"file": name, "upload": None, "analyze": None, "maps": 0, "risks": 0, "error": None}

    with open(path, "rb") as f:
        r = requests.post(
            f"{BASE}/upload-document",
            files={"file": (name, f, "application/pdf")},
            headers=headers,
            timeout=120,
        )
    if r.status_code != 200:
        result["error"] = f"upload {r.status_code}: {r.text[:200]}"
        return result
    data = r.json()
    result["upload"] = "ok"
    doc_id = data["document_id"]

    r2 = requests.post(
        f"{BASE}/analyze-document",
        params={"doc_id": doc_id},
        headers=headers,
        timeout=300,
    )
    if r2.status_code != 200:
        result["error"] = f"analyze {r2.status_code}: {r2.text[:200]}"
        result["document_id"] = doc_id
        return result
    analysis = r2.json()
    result["analyze"] = "ok"
    result["document_id"] = doc_id
    result["maps"] = len(analysis.get("maps", []))
    result["risks"] = len(analysis.get("risks", []))
    result["compliance_score"] = analysis.get("compliance_score")
    return result


def main():
    pdfs = sorted([f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")])
    print(f"Found {len(pdfs)} PDFs in {PDF_DIR}\n")
    if not pdfs:
        print("No PDFs found.")
        sys.exit(1)

    token = login()
    print("Login: OK\n")

    results = []
    for pdf in pdfs:
        path = os.path.join(PDF_DIR, pdf)
        print(f"Testing {pdf}...")
        r = run_pdf_test(path, token)
        results.append(r)
        status = "PASS" if r.get("analyze") == "ok" else "FAIL"
        print(f"  {status} upload={r.get('upload')} analyze={r.get('analyze')} maps={r.get('maps')} risks={r.get('risks')}")
        if r.get("error"):
            print(f"  Error: {r['error']}")
        print()

    passed = sum(1 for r in results if r.get("analyze") == "ok")
    print(f"SUMMARY: {passed}/{len(results)} PDFs fully analyzed")
    out = os.path.join(os.path.dirname(__file__), "batch_pdf_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
