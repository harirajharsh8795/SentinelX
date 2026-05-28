from typing import List, Optional, Dict, Any, Union
from vector_db.chroma_client import get_client
from rag.embeddings import simple_embedding, batch_embeddings


def get_collection():
    client = get_client()
    return client.get_or_create_collection(name="canara_sentinel_v4", metadata={"hnsw:space": "cosine"})


def add_chunks(
    doc_id: str,
    chunks: List[Dict[str, Any]],
    regulator: Optional[str] = None,
    framework: Optional[str] = None,
    source_url: Optional[str] = None,
    ingestion_type: str = "upload",
    document_name: Optional[str] = None,
) -> None:
    collection = get_collection()
    valid_chunks = [c for c in chunks if (c.get("text") or "").strip()]
    if not valid_chunks:
        return
    ids = [f"{doc_id}-{i}" for i in range(len(valid_chunks))]

    documents = [c["text"] for c in valid_chunks]
    embeddings = batch_embeddings(documents)

    metadatas = []
    for i, c in enumerate(valid_chunks):
        meta = {
            "doc_id": doc_id,
            "document_id": doc_id,
            "chunk_index": i,
            "section_title": c.get("section_title", "General"),
            "ingestion_type": ingestion_type or "upload",
            "source_type": ingestion_type or "upload",
        }
        if regulator:
            meta["regulator"] = regulator
        if framework:
            meta["framework"] = framework
        if source_url:
            meta["source_url"] = source_url[:500]
        if document_name:
            meta["document_name"] = document_name
        metadatas.append(meta)

    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)


def _build_where(
    doc_id: Optional[Union[str, List[str]]] = None,
    regulator: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    # Enforce active document_id to prevent database/vector contamination
    if not doc_id:
        from database.database import get_db_context
        from database.models import Document
        with get_db_context() as db:
            latest = db.query(Document).order_by(Document.upload_date.desc()).first()
            if latest:
                doc_id = latest.id
            else:
                doc_id = "NO_DOCUMENTS_FOUND"

    clauses = []
    if doc_id:
        if isinstance(doc_id, list):
            clauses.append({"doc_id": {"$in": doc_id}})
        else:
            clauses.append({"doc_id": doc_id})
    if regulator:
        clauses.append({"regulator": regulator.upper()})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def search_similar(
    query: str,
    top_k: int = 6,
    doc_id: Optional[Union[str, List[str]]] = None,
    regulator: Optional[str] = None,
) -> List[Dict[str, Any]]:
    collection = get_collection()
    query_embedding = simple_embedding(query)
    where = _build_where(doc_id, regulator)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    
    retrieved = []
    for d, m, dist in zip(docs, metas, distances):
        retrieved.append({
            "text": d,
            "metadata": m,
            "score": dist
        })
        
    return retrieved
