import os
from dotenv import load_dotenv
load_dotenv(override=True)

import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY", "")
print("API Key loaded:", api_key[:10] + "..." if api_key else "None")

if not api_key:
    print("Error: GEMINI_API_KEY environment variable is empty.")
    exit(1)

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    print("Calling gemini-2.5-flash...")
    response = model.generate_content("Hello! Are you working?")
    print("Response:")
    print(response.text)
except Exception as e:
    print("Gemini API failed with error:")
    import traceback
    traceback.print_exc()
