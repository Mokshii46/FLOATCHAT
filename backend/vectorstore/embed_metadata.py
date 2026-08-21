"""
Embed schema documentation markdown files into the Chroma vector store.

Called at startup from main.py (idempotent — skips if collection already
has documents).  Can also be run as a standalone script:

    python -m vectorstore.embed_metadata
"""

from __future__ import annotations

from pathlib import Path

from vectorstore.chroma_client import get_chroma_client
from utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_DOCS_DIR = Path(__file__).parent / "schema_docs"
CHUNK_SIZE = 800          # characters per chunk
CHUNK_OVERLAP = 100


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character chunks."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def embed_schema_docs_if_empty() -> int:
    """
    Embed all .md files from schema_docs/ only if the collection is empty.
    Returns the number of documents upserted (0 if skipped).
    """
    client = get_chroma_client()
    if client.count() > 0:
        logger.info("Vector store already populated (%d docs). Skipping embed.", client.count())
        return 0

    return embed_schema_docs(force=True)


def embed_schema_docs(force: bool = False) -> int:
    """Embed all schema doc markdown files. Pass force=True to re-embed."""
    client = get_chroma_client()

    if not force and client.count() > 0:
        logger.info("Skipping embed — %d docs already in store.", client.count())
        return 0

    md_files = sorted(SCHEMA_DOCS_DIR.glob("*.md"))
    if not md_files:
        logger.warning("No markdown files found in %s", SCHEMA_DOCS_DIR)
        return 0

    documents: list[str] = []
    ids: list[str] = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        chunks = _chunk_text(text)
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            ids.append(f"{md_file.stem}_{i}")

    client.upsert(documents=documents, ids=ids)
    logger.info("Embedded %d chunks from %d schema doc files.", len(documents), len(md_files))
    return len(documents)


if __name__ == "__main__":
    n = embed_schema_docs(force=True)
    print(f"Embedded {n} document chunks.")