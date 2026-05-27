import asyncio
import os
from database.database import engine, Base
from database.models import Document
from services.document_service import DocumentService
from rag.chunker import document_chunker
from ai_agents.orchestrator import run_autonomous_compliance_graph

# Setup DB
Base.metadata.create_all(bind=engine)

async def test_pipeline():
    print('Starting pipeline test...')
    file_path = 'test_pdfs/RBI_KYC_Test.pdf'
    
    with open('test_pdfs/RBI_KYC_Test.pdf', 'rb') as f:
        content = f.read()

    print('Uploading...')
    doc_service = DocumentService()
    # document_service.py: def save_uploaded_file(self, filename: str, content: bytes) -> str:
    # Wait, save_uploaded_file takes content
    # Let's check how document_service is structured
