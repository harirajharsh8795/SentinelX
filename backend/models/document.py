from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChunkMetadata(BaseModel):
    doc_id: str
    chunk_index: int
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    
class DocumentChunk(BaseModel):
    text: str
    metadata: ChunkMetadata

class RetrievedChunk(BaseModel):
    text: str
    metadata: Dict[str, Any]
    score: float
