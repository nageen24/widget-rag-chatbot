"""
Ingest pipeline:
  1. Load all .docx and .pdf files from data/
  2. Split into overlapping chunks
  3. Save chunks to JSON (BM25 search handles retrieval)
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docx import Document
from backend.config import ALL_SOURCE_FILES, CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP


def load_docx(path: str) -> str:
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def load_pdf(path: str) -> str:
    from pypdf import PdfReader
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages)


def load_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return load_docx(path)
    elif ext == ".pdf":
        return load_pdf(path)
    return ""


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
    if not ALL_SOURCE_FILES:
        print("ERROR: No .docx or .pdf files found in data/")
        return False

    if not force and os.path.exists(CHUNKS_FILE):
        with open(CHUNKS_FILE) as f:
            existing = json.load(f)
        print(f"  Knowledge base already built ({len(existing)} chunks). Use --force to rebuild.")
        return True

    all_text_parts = []
    for path in ALL_SOURCE_FILES:
        print(f"Loading: {os.path.basename(path)}")
        if not os.path.exists(path):
            print(f"  WARNING: File not found, skipping: {path}")
            continue
        text = load_file(path)
        if text:
            print(f"  Extracted {len(text)} characters")
            all_text_parts.append(text)
        else:
            print(f"  WARNING: No text extracted from {os.path.basename(path)}")

    if not all_text_parts:
        print("ERROR: No text extracted from any file.")
        return False

    combined = "\n\n".join(all_text_parts)
    print(f"\nTotal combined text: {len(combined)} characters from {len(all_text_parts)} file(s)")

    chunks = chunk_text(combined, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"Split into {len(chunks)} chunks")

    os.makedirs(os.path.dirname(CHUNKS_FILE), exist_ok=True)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved to: {CHUNKS_FILE}")
    print(f"\nDone. {len(chunks)} chunks ready.")
    return True


if __name__ == "__main__":
    force = "--force" in sys.argv
    ingest(force=force)
