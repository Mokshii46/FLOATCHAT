# FloatChat 🌊

> RAG-powered conversational interface for ARGO ocean float data — **SIH 2025**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61dafb?logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL+PostGIS-16-336791?logo=postgresql)](https://postgis.net)

FloatChat lets anyone — student, fisherman, or oceanographer — ask natural-language questions about ARGO float data and get instant answers with maps, charts, and plain-English explanations.

---

## 7 Unique Selling Points

| # | USP | Description |
|---|-----|-------------|
| 1 | **Anomaly Detection** | Rolling z-score flags statistically significant temperature/salinity events; auto-narrates findings |
| 2 | **Multilingual** | Works in English, Hindi, Tamil, Bengali, Telugu, Kannada, Malayalam |
| 3 | **Trajectory Prediction** | Predicts next float surfacing location using linear drift + optional ML model |
| 4 | **Voice Input** | Whisper STT — ask by speaking |
| 5 | **Explainability** | Every answer shows the generated SQL + routing logic — scientists can verify |
| 6 | **Mode Toggle** | Citizen (plain summaries) vs Researcher (raw data + QC flags + SQL) |
| 7 | **BGC-Argo** | Full support for O₂, Chlorophyll, pH, Nitrate from BGC-Argo floats |

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Anthropic API key

### 1. Clone & configure
```bash
git clone https://github.com/your-org/FloatChat.git
cd FloatChat
cp .env.example .env
# Edit .env — set LLM_API_KEY=your_anthropic_key
```

### 2. Start services
```bash
docker-compose up -d
```

### 3. Seed demo data (offline judging)
```bash
docker exec floatchat_backend python ../scripts/seed_demo_data.py --floats 5 --cycles 30
```

### 4. Open the app
- **Frontend**: http://localhost:5173
- **API docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

---

## Architecture

```
Browser → React + Vite → FastAPI Backend → PostgreSQL + PostGIS
                               ↓
                    NL2SQL Router (template | LLM)
                               ↓
                    ChromaDB (RAG, schema docs)
                               ↓
                    Anthropic Claude (SQL gen + summaries)
```

See [docs/architecture.md](docs/architecture.md) for the full system diagram.

---

## Project Structure

```
FloatChat/
├── backend/          FastAPI app, ETL, NL2SQL, services, API, ML
├── frontend/         React + Vite UI
├── data/             Raw NetCDF cache, processed parquet, schema docs
├── scripts/          DB init, demo seeder, ETL pipeline runner
├── docs/             Architecture, DB schema, demo script
└── docker-compose.yml
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Live ETL Pipeline

```bash
bash scripts/run_pipeline.sh --years 3
# or for a specific float:
bash scripts/run_pipeline.sh --wmo 2902183
```

---

## Demo Questions

- *"What is the average temperature in the Arabian Sea this year?"*
- *"Show me all active BGC floats on the map."*
- *"Chlorophyll profile for float 6904160."*
- *"Where will float 2902183 surface next?"*
- *"अरब सागर में लवणता कितनी है?"* (Hindi)

See [docs/demo_script.md](docs/demo_script.md) for the full rehearsed demo sequence.

---

## License

MIT — see [LICENSE](LICENSE)
