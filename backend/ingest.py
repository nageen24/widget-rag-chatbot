"""
Ingest pipeline:
  1. Load Word document
  2. Split into overlapping chunks
  3. Save chunks to JSON (no vector DB needed — BM25 search handles retrieval)
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docx import Document
from backend.config import WORD_FILE, CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP


def load_word_doc(path: str) -> str:
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def ingest(force: bool = False):
    print(f"Loading document: {WORD_FILE}")
    if not os.path.exists(WORD_FILE):
        print(f"ERROR: File not found: {WORD_FILE}")
        return False

    if not force and os.path.exists(CHUNKS_FILE):
        with open(CHUNKS_FILE) as f:
            existing = json.load(f)
        print(f"  Knowledge base already built ({len(existing)} chunks). Use --force to rebuild.")
        return True

    raw_text = load_word_doc(WORD_FILE)
    print(f"  Extracted {len(raw_text)} characters")

    chunks = chunk_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"  Split into {len(chunks)} chunks")

    os.makedirs(os.path.dirname(CHUNKS_FILE), exist_ok=True)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"  Saved to: {CHUNKS_FILE}")
    print(f"\nDone. {len(chunks)} chunks ready.")
    return True


if __name__ == "__main__":
    force = "--force" in sys.argv
    ingest(force=force)
