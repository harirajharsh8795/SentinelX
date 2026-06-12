import sys
import asyncio
import traceback

sys.path.append("e:/Desktop/CANARA SENTINEL AI/backend")

from database.database import get_db_context
from database.models import Document
from services.document_service import analyze_document

async def main():
    doc_id = "69255f28-7624-46bf-a5ad-04279dd44010"
    print(f"Analyzing doc: {doc_id}...")
    try:
        res = await analyze_document(doc_id)
        print("Success! Result keys:", res.keys())
    except Exception as e:
        print("EXCEPTION RAISED:")
        print(type(e).__name__)
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
