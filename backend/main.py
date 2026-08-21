"""
FloatChat — FastAPI application entrypoint.

Startup sequence
----------------
1. PostGIS extension + ORM tables are created (idempotent).
2. Vector store is initialised; schema docs are embedded if the collection is empty.
3. APScheduler background job is started for nightly ARGO refresh.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────
    logger.info("FloatChat backend starting …")

    # 1. Database / PostGIS
    init_db()
    logger.info("Database initialised.")

    # 2. Vector store (embed schema docs if collection is empty)
    try:
        from vectorstore.embed_metadata import embed_schema_docs_if_empty
        embed_schema_docs_if_empty()
        logger.info("Vector store ready.")
    except Exception as exc:
        logger.warning("Vector store init skipped: %s", exc)

    # 3. Scheduler (nightly ARGO refresh)
    try:
        from etl.scheduler import start_scheduler
        scheduler = start_scheduler()
        logger.info("Scheduler started.")
    except Exception as exc:
        logger.warning("Scheduler not started: %s", exc)
        scheduler = None

    yield  # ── running ──────────────────────────────────────────

    # ── Shutdown ──────────────────────────────────────────────────
    if scheduler:
        scheduler.shutdown(wait=False)
    logger.info("FloatChat backend stopped.")


app = FastAPI(
    title="FloatChat API",
    description="RAG-powered conversational interface for ARGO ocean float data.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
from api.health import router as health_router
from api.floats import router as floats_router
from api.chat import router as chat_router
from api.query import router as query_router
from api.viz import router as viz_router
from api.voice import router as voice_router
from api.export import router as export_router

app.include_router(health_router, tags=["health"])
app.include_router(floats_router, prefix="/floats", tags=["floats"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(query_router, prefix="/query", tags=["query"])
app.include_router(viz_router, prefix="/viz", tags=["viz"])
app.include_router(voice_router, prefix="/voice", tags=["voice"])
app.include_router(export_router, prefix="/export", tags=["export"])