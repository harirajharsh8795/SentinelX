import chromadb
from utils.config import settings

_client = None


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        import os
        _client = chromadb.PersistentClient(path=os.path.abspath(settings.chroma_persist_dir))
    return _client
