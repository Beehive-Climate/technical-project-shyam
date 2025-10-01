from typing import List, Tuple, Optional
from docx import Document

_DB_DOC_CACHE: Optional[str] = None

# This is to load the reference database file for context
def load_doc_from_db(file_path) -> str:
    # cache it globally for referrencing it for the results later
    global _DB_DOC_CACHE
    if _DB_DOC_CACHE is not None:
        return _DB_DOC_CACHE
    doc = Document(file_path)
    parts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)
    _DB_DOC_CACHE = "\n".join(parts)
    return _DB_DOC_CACHE