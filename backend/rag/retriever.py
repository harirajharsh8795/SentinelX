import re
from typing import List, Optional, Dict, Any, Union
from vector_db.chroma_client import get_client
from rag.embeddings import simple_embedding
from utils.logger import get_logger
from services.event_broadcaster import event_bus

logger = get_logger(__name__)


def get_collection(doc_id: str):
    client = get_client()
    # Sanitize doc_id to conform to ChromaDB collection name rules (3-63 chars, alphanumeric, _ or -)
    sanitized_name = doc_id
    if not sanitized_name:
        sanitized_name = "default_collection"
    sanitized_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', sanitized_name)
    if len(sanitized_name) < 3:
        sanitized_name = (sanitized_name + "___")[:3]
    elif len(sanitized_name) > 63:
        sanitized_name = sanitized_name[:63]
        
    return client.get_or_create_collection(name=sanitized_name, metadata={"hnsw:space": "cosine"})


def add_chunks(
    doc_id: str,
    chunks: List[Dict[str, Any]],
    regulator: Optional[str] = None,
    framework: Optional[str] = None,
    source_url: Optional[str] = None,
    ingestion_type: str = "upload",
    document_name: Optional[str] = None,
) -> None:
    collection = get_collection(doc_id)
    valid_chunks = [c for c in chunks if (c.get("text") or "").strip()]
    if not valid_chunks:
        return

    documents = []
    embeddings = []
    metadatas = []
    
    total_valid = len(valid_chunks)
    logger.info(f"Starting batch vector embedding generation for {total_valid} chunks.")

    # Use batch embedding API for speed (sends multiple chunks to Ollama at once)
    from rag.embeddings import batch_embeddings
    
    texts = [c["text"] for c in valid_chunks]
    batch_size = 16  # Smaller batches for Jetson memory constraints
    
    for batch_start in range(0, total_valid, batch_size):
        batch_end = min(batch_start + batch_size, total_valid)
        batch_texts = texts[batch_start:batch_end]
        batch_chunks = valid_chunks[batch_start:batch_end]
        
        try:
            batch_embs = batch_embeddings(batch_texts, batch_size=batch_size)
            
            for j, (emb, c) in enumerate(zip(batch_embs, batch_chunks)):
                if emb:
                    idx = batch_start + j
                    documents.append(c["text"])
                    embeddings.append(emb)
                    
                    meta = {
                        "doc_id": doc_id,
                        "document_id": doc_id,
                        "chunk_index": len(documents) - 1,
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
                    
        except Exception as e:
            logger.warning(f"Batch embedding failed for chunks {batch_start}-{batch_end}: {e}. Falling back to individual embedding.")
            # Fallback: process failed batch chunks one by one
            for j, c in enumerate(batch_chunks):
                try:
                    emb = simple_embedding(c["text"], timeout=45.0)
                    if emb:
                        documents.append(c["text"])
                        embeddings.append(emb)
                        meta = {
                            "doc_id": doc_id,
                            "document_id": doc_id,
                            "chunk_index": len(documents) - 1,
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
                except Exception as e2:
                    logger.error(f"Skipping chunk {batch_start + j} due to embedding failure: {e2}")
                    continue

        # Send progress WebSocket update per batch
        percent = int((batch_end / total_valid) * 100)
        event_bus.emit(
            "system_info", 
            f"Embedding generation: {percent}% ({batch_end}/{total_valid} chunks processed)", 
            doc_id=doc_id
        )

    if documents:
        ids = [f"{doc_id}-{idx}" for idx in range(len(documents))]
        collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        
        # Count verify after add_chunks
        try:
            count = collection.count()
            logger.info(f"Verified count in collection '{doc_id}' after ingestion: {count} chunks indexed.")
        except Exception as e:
            logger.warning(f"Failed to verify collection count: {e}")


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
    # Resolve active doc_id if not provided
    if not doc_id:
        from database.database import get_db_context
        from database.models import Document
        with get_db_context() as db:
            latest = db.query(Document).order_by(Document.upload_date.desc()).first()
            if latest:
                doc_id = latest.id
            else:
                doc_id = "default_collection"

    query_embedding = simple_embedding(query, timeout=45.0)

    # If doc_id is a list of strings, query each collection and combine results
    if isinstance(doc_id, list):
        all_results = []
        for d in doc_id:
            try:
                collection = get_collection(d)
                # Filter by regulator if provided
                where = {"regulator": regulator.upper()} if regulator else None
                
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where,
                    include=["documents", "metadatas", "distances"]
                )
                
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                
                for doc_text, m, dist in zip(docs, metas, distances):
                    all_results.append({
                        "text": doc_text,
                        "metadata": m,
                        "score": dist
                    })
            except Exception as e:
                logger.error(f"Error querying collection {d}: {e}")
                continue
                
        # Sort combined results by score ascending (lower distance is better)
        all_results.sort(key=lambda x: x["score"])
        return all_results[:top_k]

    else:
        collection = get_collection(doc_id)
        where = {"regulator": regulator.upper()} if regulator else None
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        retrieved = []
        for d_text, m, dist in zip(docs, metas, distances):
            retrieved.append({
                "text": d_text,
                "metadata": m,
                "score": dist
            })
            
        return retrieved
