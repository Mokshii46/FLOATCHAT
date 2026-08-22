"""
Chroma vector store client — thin wrapper used by NL2SQL and chat service.

The collection "floatchat_schema" stores chunks from the markdown schema docs
under vectorstore/schema_docs/. At query time, the top-k most relevant chunks
are returned and injected into the LLM prompt.
"""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import chromadb
# pyrefly: ignore [missing-import]
from chromadb.config import Settings as ChromaSettings

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "floatchat_schema"


class ChromaClient:
    """Singleton-style Chroma client with lazy sentence-transformer embeddings."""

    _instance: ChromaClient | None = None

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.vector_db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._encoder = None
        logger.info(
            "ChromaClient ready — collection '%s' has %d docs.",
            COLLECTION_NAME,
            self._collection.count(),
        )

    def _get_encoder(self):
        if self._encoder is None:
            try:
                # pyrefly: ignore [missing-import]
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer(settings.embedding_model)
            except Exception as exc:
                logger.warning("Could not load SentenceTransformer (%s). Using fallback embeddings.", exc)
                self._encoder = False
        return self._encoder

    @classmethod
    def get(cls) -> ChromaClient:
        if cls._instance is None:
            cls._instance = ChromaClient()
        return cls._instance

    # ── write ─────────────────────────────────────────────────────

    def upsert(self, documents: list[str], ids: list[str]) -> None:
        encoder = self._get_encoder()
        if encoder:
            embeddings = encoder.encode(documents, show_progress_bar=False).tolist()
            self._collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
            )
        else:
            self._collection.upsert(
                ids=ids,
                documents=documents,
            )
        logger.info("Upserted %d documents to vector store.", len(documents))

    # ── read ──────────────────────────────────────────────────────

    def get_relevant_context(self, query: str, top_k: int = 5) -> str:
        """
        Return top-k most similar schema doc chunks concatenated as a single
        string, ready for prompt injection.
        """
        if self._collection.count() == 0:
            return ""

        encoder = self._get_encoder()
        if encoder:
            embedding = encoder.encode([query], show_progress_bar=False).tolist()
            results = self._collection.query(
                query_embeddings=embedding,
                n_results=min(top_k, self._collection.count()),
            )
        else:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, self._collection.count()),
            )

        chunks = results.get("documents", [[]])[0]
        return "\n\n---\n\n".join(chunks)

    def count(self) -> int:
        return self._collection.count()


# Module-level convenience accessor
def get_chroma_client() -> ChromaClient:
    return ChromaClient.get()