import requests
import json
from pathlib import Path

pdf_path = 'PDF FOR TEST/CYBERSECURITYRBI.pdf'

# Check if file exists
if not Path(pdf_path).exists():
    print(f'ERROR: {pdf_path} not found')
    exit(1)

print('Step 1: Authenticating and uploading PDF...')
try:
    print('Logging in to acquire access token...')
    login_resp = requests.post(
        'http://127.0.0.1:8000/api/auth/token',
        data={"username": "admin", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if login_resp.status_code != 200:
        print(f'Login failed: {login_resp.status_code} - {login_resp.text}')
        exit(1)
    
    token = login_resp.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}

    print('Step 2: Uploading PDF with auth token...')
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path, f, 'application/pdf')}
        r = requests.post('http://127.0.0.1:8000/api/upload-document', headers=headers, files=files)
    
    if r.status_code != 200:
        print(f'Upload failed with status {r.status_code}: {r.text}')
        exit(1)
    
    upload_resp = r.json()
    print(f'Upload response: {json.dumps(upload_resp, indent=2)}')
    doc_id = upload_resp.get('document_id')
    
    if not doc_id:
        print('ERROR: No document_id in upload response')
        exit(1)
    
    print(f'\nStep 3: Analyzing document (ID: {doc_id})...')
    r2 = requests.post('http://127.0.0.1:8000/api/analyze-document', headers=headers, params={'doc_id': doc_id})
    
    if r2.status_code != 200:
        print(f'Analysis failed with status {r2.status_code}: {r2.text}')
        exit(1)
    
    analysis_resp = r2.json()
    print(f'\nStep 4: Analysis Results:')
    print(f'Compliance Score: {analysis_resp.get("compliance_score")}')
    print(f'Risk Score: {analysis_resp.get("risk_score")}')
    summary = analysis_resp.get('summary', 'N/A')
    if isinstance(summary, str) and len(summary) > 200:
        print(f'Summary: {summary[:200]}...')
    else:
        print(f'Summary: {summary}')
    print(f'\nFull Response:')
    print(json.dumps(analysis_resp, indent=2))

except Exception as e:
    print(f'ERROR: {str(e)}')
    import traceback
    traceback.print_exc()
