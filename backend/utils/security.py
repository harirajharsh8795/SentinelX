import os
import re

ALLOWED_EXTENSIONS = {".pdf"}


def sanitize_filename(filename: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return name[:120]


def ensure_upload_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)
