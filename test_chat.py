import sys
import os

# Add backend directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.services.chat_service import chat_with_document

def test_chat():
    from backend.database.database import engine
    from backend.database import models
    from backend.database.migrate import run_migrations
    models.Base.metadata.create_all(bind=engine)
    run_migrations()

    doc_id = "test-doc-id"
    # Note: Requires an actual document in Chroma to return real facts, but we are testing connectivity.
    print("Testing Chat with RAG Pipeline...")
    res = chat_with_document(doc_id, "What are the penalties mentioned?")
    print("AI Response:", res["reply"])
    print("Sources Found:", len(res["sources"]))

if __name__ == "__main__":
    test_chat()