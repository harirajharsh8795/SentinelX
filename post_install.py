#!/usr/bin/env python3
import os
import sys

def patch_chromadb():
    print("======================================================")
    print("      SentinelX - ChromaDB Post-Installation Patcher  ")
    print("======================================================")
    
    try:
        import chromadb
    except ImportError:
        print("[ERROR] ChromaDB is not installed in the current Python environment.")
        print("[ERROR] Please activate your virtual environment (.venv) first and run:")
        print("        pip install -r backend/requirements.txt")
        sys.exit(1)
        
    chromadb_dir = os.path.dirname(chromadb.__file__)
    print(f"[INFO] ChromaDB package located at: {chromadb_dir}")
    
    # 1. Patch sqlite.py
    sqlite_file = os.path.join(chromadb_dir, "segment", "impl", "metadata", "sqlite.py")
    if not os.path.exists(sqlite_file):
        print(f"[WARNING] sqlite.py not found at expected path: {sqlite_file}")
    else:
        print(f"[INFO] Patching {sqlite_file}...")
        with open(sqlite_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        target_marker = 'def _decode_seq_id(seq_id_bytes: bytes) -> SeqId:\n    """Decode a byte array into a SeqID"""'
        patch_code = '\n    if isinstance(seq_id_bytes, int):\n        return seq_id_bytes'
        
        if "if isinstance(seq_id_bytes, int):" in content:
            print("[INFO] sqlite.py is already patched. Skipping.")
        elif target_marker in content:
            patched_content = content.replace(target_marker, target_marker + patch_code)
            with open(sqlite_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(patched_content)
            print("[SUCCESS] sqlite.py patched successfully!")
        else:
            print("[ERROR] Could not find the signature of _decode_seq_id in sqlite.py. Skipping.")
            
    # 2. Patch local_persistent_hnsw.py
    hnsw_file = os.path.join(chromadb_dir, "segment", "impl", "vector", "local_persistent_hnsw.py")
    if not os.path.exists(hnsw_file):
        print(f"[WARNING] local_persistent_hnsw.py not found at expected path: {hnsw_file}")
    else:
        print(f"[INFO] Patching {hnsw_file}...")
        with open(hnsw_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        target_marker = """            self._persist_data = PersistentData.load_from_file(
                self._get_metadata_file()
            )
            self._dimensionality = self._persist_data.dimensionality"""
            
        patch_code = """            self._persist_data = PersistentData.load_from_file(
                self._get_metadata_file()
            )
            if isinstance(self._persist_data, dict):
                d = self._persist_data
                self._persist_data = PersistentData(
                    dimensionality=d.get("dimensionality"),
                    total_elements_added=d.get("total_elements_added", 0),
                    total_elements_updated=d.get("total_elements_updated", 0),
                    total_invalid_operations=d.get("total_invalid_operations", 0),
                    max_seq_id=d.get("max_seq_id", 0),
                    id_to_label=d.get("id_to_label", {}),
                    label_to_id=d.get("label_to_id", {}),
                    id_to_seq_id=d.get("id_to_seq_id", {}),
                )
            self._dimensionality = self._persist_data.dimensionality"""
            
        if "if isinstance(self._persist_data, dict):" in content:
            print("[INFO] local_persistent_hnsw.py is already patched. Skipping.")
        elif target_marker in content:
            patched_content = content.replace(target_marker, patch_code)
            with open(hnsw_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(patched_content)
            print("[SUCCESS] local_persistent_hnsw.py patched successfully!")
        else:
            # Fallback block matching if format/newlines differ slightly
            target_marker_alt = "self._persist_data = PersistentData.load_from_file(\n                self._get_metadata_file()\n            )\n            self._dimensionality = self._persist_data.dimensionality"
            patch_code_alt = "self._persist_data = PersistentData.load_from_file(\n                self._get_metadata_file()\n            )\n            if isinstance(self._persist_data, dict):\n                d = self._persist_data\n                self._persist_data = PersistentData(\n                    dimensionality=d.get(\"dimensionality\"),\n                    total_elements_added=d.get(\"total_elements_added\", 0),\n                    total_elements_updated=d.get(\"total_elements_updated\", 0),\n                    total_invalid_operations=d.get(\"total_invalid_operations\", 0),\n                    max_seq_id=d.get(\"max_seq_id\", 0),\n                    id_to_label=d.get(\"id_to_label\", {}),\n                    label_to_id=d.get(\"label_to_id\", {}),\n                    id_to_seq_id=d.get(\"id_to_seq_id\", {}),\n                )\n            self._dimensionality = self._persist_data.dimensionality"
            if target_marker_alt in content:
                patched_content = content.replace(target_marker_alt, patch_code_alt)
                with open(hnsw_file, "w", encoding="utf-8", newline="\n") as f:
                    f.write(patched_content)
                print("[SUCCESS] local_persistent_hnsw.py patched successfully (via alternate match)!")
            else:
                print("[ERROR] Could not find the metadata loading block in local_persistent_hnsw.py. Skipping.")

    print("======================================================")
    print("              Patches Application Finished            ")
    print("======================================================")

if __name__ == "__main__":
    patch_chromadb()
