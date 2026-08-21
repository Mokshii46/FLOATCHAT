# FloatChat Architecture

## System Overview

FloatChat is a RAG-powered conversational interface for ARGO ocean float data, built for SIH 2025.

```
User (Browser)
    │  HTTP/WS
    ▼
┌─────────────────────┐
│   React + Vite      │  ← ChatPanel, MapView, Charts, USP components
│   Frontend          │
└──────────┬──────────┘
           │ REST API (JSON)
           ▼
┌─────────────────────┐
│   FastAPI Backend   │  ← main.py, api/ routers
│                     │
│  ┌───────────────┐  │
│  │ chat_service  │  │  ← Orchestration hub (all USPs)
│  └──────┬────────┘  │
│         │           │
│  ┌──────▼────────┐  │
│  │  NL2SQL       │  │  ← router → template or LLM
│  │  router       │  │
│  └──────┬────────┘  │
│         │           │
│  ┌──────▼────────┐  │  ┌────────────────┐
│  │  Chroma       │◄─┼──┤  Schema Docs   │
│  │  (RAG)        │  │  │  (3 md files)  │
│  └───────────────┘  │  └────────────────┘
│                     │
│  ┌───────────────┐  │
│  │  Claude LLM   │  │  ← SQL gen + summaries + translation
│  └───────────────┘  │
│                     │
│  ┌───────────────┐  │
│  │  query_service│  │  ← Read-only SQL execution
│  └──────┬────────┘  │
└─────────┼───────────┘
          │
          ▼
┌─────────────────────┐
│  PostgreSQL +       │
│  PostGIS            │
│                     │
│  float_metadata     │
│  profiles           │
│  trajectory_points  │
│  bgc_profiles       │
└─────────────────────┘
```

## Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `main.py` | FastAPI app, lifespan, CORS, router mounting |
| `api/` | HTTP route handlers, request/response models |
| `services/chat_service.py` | Orchestrates all USPs end-to-end |
| `nl2sql/router.py` | Template matching → LLM fallback |
| `nl2sql/sql_validator.py` | SQL safety (read-only enforcement) |
| `vectorstore/` | Chroma RAG index; schema doc embeddings |
| `etl/` | ARGO data fetch, parse, QC, load |
| `ml/` | Trajectory prediction, anomaly detection |
| `services/` | Individual USP implementations |

## Data Flow

```
User Question
    ↓ detect_language
    ↓ translate_to_english      (USP 2)
    ↓ router.route()
        ├─ Template match → fill params → SQL
        └─ LLM match → RAG context → Claude → SQL
    ↓ sql_validator.validate()
    ↓ query_service.execute_query()
    ↓ viz_service.shape_results()
    ↓ generate_summary() → Claude
    ↓ translate_from_english    (USP 2)
    ↓ anomaly_service (async)   (USP 1)
    ↓ explainability payload    (USP 5)
    → ChatResponse JSON
```

## Deployment

### Local Development
```bash
docker-compose up
```

### Production
- Backend: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2`
- Frontend: `npm run build` then serve `dist/` via Nginx
- Database: PostGIS 16-3.4 on managed Postgres
