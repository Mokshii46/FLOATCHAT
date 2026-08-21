"""
Thin wrapper around Chroma (persistent, local — no server needed) used to
ground the NL2SQL LLM call in the real schema instead of letting it guess
column names.

Two collections:
  - "schema_docs"      populated once from vectorstore/schema_docs/*.md
  - "float_summaries"  populated/refreshed from live float_metadata rows
                        (embed_metadata.py), so the LLM can resolve fuzzy
                        float references like "the float near Mumbai" or
                        "INCOIS floats" without a separate DB round trip.

If settings.vector_db_backend != "chroma", get_relevant_context() falls
back to returning the raw schema_docs concatenated (still correct, just
skips the similarity ranking) so the rest of the pipeline never breaks
because of vector store config.
"""

from __future__ import annotations

import logging
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

SCHEMA_DOCS_DIR = Path(__file__).resolve().parent / "schema_docs"

_client = None
_schema_collection = None
_float_collection = None


def _get_client():
    global _client
    if _client is None:
        import chromadb

        Path(settings.vector_db_path).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.vector_db_path)
    return _client


def _get_embedding_fn():
    from chromadb.utils import embedding_functions

    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.embedding_model
    )


def get_schema_collection():
    global _schema_collection
    if _schema_collection is None:
        client = _get_client()
        _schema_collection = client.get_or_create_collection(
            name="schema_docs", embedding_function=_get_embedding_fn()
        )
    return _schema_collection


def get_float_collection():
    global _float_collection
    if _float_collection is None:
        client = _get_client()
        _float_collection = client.get_or_create_collection(
            name="float_summaries", embedding_function=_get_embedding_fn()
        )
    return _float_collection


def _fallback_all_schema_docs() -> str:
    """Used if chroma isn't reachable — just dump every schema doc raw."""
    chunks = []
    for path in sorted(SCHEMA_DOCS_DIR.glob("*.md")):
        chunks.append(path.read_text())
    return "\n\n---\n\n".join(chunks)


def get_relevant_context(query: str, n_results: int = 3, include_floats: bool = True) -> str:
    """
    Returns concatenated markdown context to inject into the NL2SQL prompt:
    the most relevant schema doc chunks, plus (optionally) any float
    summaries that fuzzy-match named floats/regions in the query.
    """
    if settings.vector_db_backend != "chroma":
        return _fallback_all_schema_docs()

    try:
        schema_coll = get_schema_collection()
        if schema_coll.count() == 0:
            logger.warning("schema_docs collection is empty — run vectorstore/embed_metadata.py first")
            return _fallback_all_schema_docs()

        results = schema_coll.query(query_texts=[query], n_results=min(n_results, schema_coll.count()))
        docs = results.get("documents", [[]])[0]
        context = "\n\n---\n\n".join(docs)

        if include_floats:
            float_coll = get_float_collection()
            if float_coll.count() > 0:
                fr = float_coll.query(query_texts=[query], n_results=min(3, float_coll.count()))
                fdocs = fr.get("documents", [[]])[0]
                if fdocs:
                    context += "\n\n---\n\nRelevant floats:\n" + "\n".join(fdocs)

        return context
    except Exception:
        logger.exception("Chroma query failed, falling back to raw schema docs")
        return _fallback_all_schema_docs()