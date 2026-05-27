import requests
import json
import traceback

def main():
    login_url = "http://127.0.0.1:8000/api/auth/token"
    upload_url = "http://127.0.0.1:8000/api/upload-document"
    pdf_path = "PDF FOR TEST/CYBERSECURITYRBI.pdf"

    print("Step 1: Logging in as officer...")
    try:
        login_data = {
            "username": "officer",
            "password": "password123"
        }
        r = requests.post(login_url, data=login_data)
        if r.status_code != 200:
            print(f"Login failed: {r.status_code} - {r.text}")
            return
        
        token = r.json().get("access_token")
        print("Login successful! Token acquired.")
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        print("\nStep 2: Uploading PDF with auth token...")
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path, f, "application/pdf")}
            r_upload = requests.post(upload_url, headers=headers, files=files)
            
        print(f"Upload Response Status Code: {r_upload.status_code}")
        print(f"Upload Response Content: {r_upload.text}")
        
    except Exception as e:
        print(f"Exception encountered: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
