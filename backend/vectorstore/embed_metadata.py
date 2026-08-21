"""
Populates the two Chroma collections used by chroma_client.py:

  1. schema_docs      — one chunk per markdown file in schema_docs/, so the
                         NL2SQL prompt gets the right table docs for the
                         question ("temperature" -> profiles.md, not bgc).
  2. float_summaries   — one short text summary per float in float_metadata,
                         so the LLM can resolve "the INCOIS float near the
                         equator" style references without extra DB calls.

Run standalone: `python -m vectorstore.embed_metadata`
Safe to re-run — collections are wiped and rebuilt each time (small data,
cheap to redo; avoids drift between the DB and the vector store).
"""

from __future__ import annotations

import logging
from pathlib import Path

from database import session_scope
from models import FloatMetadata
from vectorstore.chroma_client import (
    SCHEMA_DOCS_DIR,
    get_schema_collection,
    get_float_collection,
)

logger = logging.getLogger(__name__)


def embed_schema_docs() -> int:
    collection = get_schema_collection()

    existing = collection.get()["ids"]
    if existing:
        collection.delete(ids=existing)

    ids, docs, metadatas = [], [], []
    for path in sorted(SCHEMA_DOCS_DIR.glob("*.md")):
        table_name = path.stem
        ids.append(f"schema::{table_name}")
        docs.append(path.read_text())
        metadatas.append({"table": table_name, "source": str(path)})

    if docs:
        collection.add(ids=ids, documents=docs, metadatas=metadatas)

    logger.info("Embedded %d schema doc chunks", len(docs))
    return len(docs)


def _float_summary(f: FloatMetadata) -> str:
    kind = "BGC" if f.is_bgc else "core"
    parts = [
        f"Float WMO {f.wmo_id} ({kind} float, platform {f.platform_type or 'unknown'}).",
        f"Operated by DAC '{f.dac}'." if f.dac else "",
        f"Project: {f.project_name}." if f.project_name else "",
        f"PI: {f.pi_name}." if f.pi_name else "",
        f"Deployed {f.deploy_date} near ({f.deploy_lat}, {f.deploy_lon})."
        if f.deploy_date
        else "",
        f"Status: {f.status}.",
    ]
    return " ".join(p for p in parts if p)


def embed_float_summaries(batch_size: int = 500) -> int:
    collection = get_float_collection()

    existing = collection.get()["ids"]
    if existing:
        collection.delete(ids=existing)

    count = 0
    with session_scope() as db:
        floats = db.query(FloatMetadata).all()
        ids, docs, metadatas = [], [], []
        for f in floats:
            ids.append(f"float::{f.wmo_id}")
            docs.append(_float_summary(f))
            metadatas.append({"wmo_id": f.wmo_id, "is_bgc": f.is_bgc, "status": f.status})
            count += 1

            if len(ids) >= batch_size:
                collection.add(ids=ids, documents=docs, metadatas=metadatas)
                ids, docs, metadatas = [], [], []

        if ids:
            collection.add(ids=ids, documents=docs, metadatas=metadatas)

    logger.info("Embedded %d float summaries", count)
    return count


def embed_all() -> None:
    n_schema = embed_schema_docs()
    n_floats = embed_float_summaries()
    logger.info("Vector store ready: %d schema chunks, %d float summaries", n_schema, n_floats)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    embed_all()