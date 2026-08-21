"""FastAPI entrypoint. Wires up routers, CORS, and startup DB init."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from utils.logger import get_logger

from api import health  # more routers (chat, query, floats, viz, voice, export) land in later phases

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FloatChat backend (env=%s)", settings.app_env)
    init_db()
    yield
    logger.info("Shutting down FloatChat backend")


app = FastAPI(
    title="FloatChat API",
    description="RAG-powered conversational interface for ARGO ocean float data",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
# app.include_router(chat.router)     # Phase 5
# app.include_router(query.router)    # Phase 5
# app.include_router(floats.router)   # Phase 5
# app.include_router(viz.router)      # Phase 5
# app.include_router(voice.router)    # USP 4
# app.include_router(export.router)   # Phase 6


@app.get("/")
def root():
    return {
        "name": "FloatChat API",
        "status": "running",
        "docs": "/docs",
    }