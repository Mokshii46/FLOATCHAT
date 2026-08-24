# FloatChat 🌊
> **AI-Powered Conversational Ocean Intelligence Platform for Global ARGO Float Data**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61dafb?style=flat-square&logo=react)](https://react.dev)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9-199900?style=flat-square&logo=leaflet)](https://leafletjs.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://postgresql.org)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite)](https://sqlite.org)
[![Tests](https://img.shields.io/badge/Tests-49%20Passed%20(100%25)-success?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

**FloatChat** transforms complex global oceanographic observations from the **International ARGO Program** into accessible, real-time conversational intelligence. Whether you are an oceanographer inspecting sensor quality flags, an educator teaching marine climate, or a fisherman asking about coastal sea surface temperatures, FloatChat delivers instant data visualizations, statistical anomaly detection, and natural language explanations.

---

## 🌟 Core Features & Dual-Mode Persona Architecture

FloatChat features a dual-persona interface tailored to different audiences:

```
                      ┌────────────────────────────────────────┐
                      │          FloatChat Dual Engine         │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
      🧭 Explorer Mode (Citizen)                      🔬 Researcher Mode (Scientist)
  ─────────────────────────────────               ─────────────────────────────────────
  • Plain-language conversational answers         • Raw DataTable with ARGO QC flags (1-4)
  • Web Speech voice input STT                    • Always-on inline SQL & explainability
  • 💡 "Did you know?" ocean fact cards           • 🏛️ Academic Provenance footer (PI, DAC, Project)
  • 🎲 "Surprise Me!" random float journey stories • Multi-float vertical depth bin comparison
  • Friendly map popups ("Ask about this float")  • Thermocline depth & MLD gradient calculations
  • 4-step first-visit guided walkthrough tour    • Full-precision CSV dataset export
```

---

## 🗺️ 360° Infinite Continuous Float Fleet Map

- **Global 360° Multi-World Wrapping**: Seamless horizontal navigation across all longitudes (`WRAP_OFFSETS = [-720, -360, 0, 360, 720]`) with `worldCopyJump`.
- **Polar Bounds Clamping**: Strict vertical bounds `[-85°, 85°]` prevent dragging into void space at polar caps.
- **Dynamic Zoom-Scaled Markers**: Indigo markers for Core ARGO, Cyan for BGC-Argo, and Glowing Amber for focused/queried floats.
- **7 World Ocean Badges**: Interactive markers for Indian Ocean, Arabian Sea, Bay of Bengal, North/South Atlantic, North/South Pacific, Southern Ocean, and Arctic Ocean.
- **Universal View Switcher**: Instant top-bar toggle between **Map View**, **Graphical Viz (Time-Series / Depth Profiles)**, and **Raw QC Data Tables**.

---

## 🧠 Hybrid NL2SQL & RAG Engine

```
User Query (Text / Voice)
   │
   ▼
[Language Detector & Translator] ── (Supports English, Hindi, Tamil, Bengali, Telugu, Kannada, Malayalam)
   │
   ▼
[NL2SQL Router]
   ├── 1. Template Match (~18 zero-latency SQL templates for SST, MLD, trajectories, BGC)
   └── 2. ChromaDB RAG Vector Store + LLM NL2SQL Fallback
           │
           ▼
[AST SQL Validator] ── (Enforces SELECT only, query limits, blocks mutation & injection)
   │
   ▼
[Database Execution (SQLite / PostGIS)]
   │
   ├── [Anomaly Detector (Rolling Z-Score on Regional Basins)]
   ├── [Viz Shaper (GeoJSON Map / DepthProfile / TimeSeries / StatCard / DataTable)]
   └── [LLM Response Synthesizer (Mode-tailored: Citizen vs Researcher)]
```

---

## 🚀 Quick Start & Local Setup

### Prerequisites
- **Python 3.10+** (Python 3.13 supported)
- **Node.js 18+** & `npm`
- **Groq API Key** or **Anthropic Claude API Key**

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/your-username/FloatChat.git
cd FloatChat

# Create & activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-120b
DATABASE_URL=sqlite:///backend/floatchat.db
```

### 3. Start Backend Server
```bash
cd backend
python -m uvicorn main:app --port 8000 --reload
```
*Backend API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)*

### 4. Start Frontend Client
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Frontend interface available at: [http://localhost:5173](http://localhost:5173)*

---

## 🧪 Running Tests

The test suite validates data ingestion, anomaly detection, AST SQL validation, routing, and REST endpoints:

```bash
cd backend
pytest tests/ -v
```

**Results**: `49 passed, 0 failures` (100% pass rate).

---

## 📂 Project Structure

```
FloatChat/
├── backend/
│   ├── api/                  # FastAPI routers (chat, floats, health, query, viz, voice, export)
│   ├── database.py           # SQLAlchemy database session & SQLite/PostGIS connection
│   ├── floatchat.db          # Pre-seeded SQLite database with 473 floats and profiles
│   ├── main.py               # Application entrypoint & startup lifespans
│   ├── ml/                   # Statistical rolling z-score anomaly detector
│   ├── models/               # ORM models (FloatMetadata, Profile, BGCProfile, TrajectoryPoint)
│   ├── nl2sql/               # Keyword router, 18 SQL templates, AST validator, query generator
│   ├── services/             # Chat, explainability, provenance, viz, and translation services
│   ├── tests/                # Comprehensive 49-test pytest suite
│   ├── utils/                # LLM client, logger, and formatters
│   └── vectorstore/          # ChromaDB client and schema embeddings for RAG
├── frontend/
│   ├── src/
│   │   ├── api/client.js     # Axios API connector
│   │   ├── components/       # MapView, ChatPanel, DataTable, GuidedTour, ExplainabilityPanel, etc.
│   │   ├── hooks/            # useChat, useVoice (STT Web Speech)
│   │   ├── pages/            # Dashboard, Home, About
│   │   └── i18n.js           # Multilingual translation dictionaries
│   ├── index.html            # Complete design system tokens, typography, and styling
│   └── package.json
└── README.md
```

---

## 💬 Example Queries to Try

### 🧭 Explorer Mode
- *"Surprise me! Pick a random active ARGO float and tell me its story in one sentence."*
- *"What's the ocean temperature near India?"*
- *"Which floats are in the Arabian Sea?"*
- *"Is there anything unusual in the Bay of Bengal?"*
- *"Show me all active floats on the map."*

### 🔬 Researcher Mode
- *"Show depth profile and QC flags for float 2905105"*
- *"Calculate thermocline depth and MLD for float 2905105"*
- *"Compare floats 2905105 and 2902183 across depth bins"*
- *"List all BGC floats with sensors and deployment dates"*
- *"Temperature anomaly in Bay of Bengal with z-scores"*

---

## 📜 Academic Attribution & Provenance

FloatChat utilizes observational data collected and made freely available by the **International Argo Program** and national contributing agencies ([https://argo.ucsd.edu](https://argo.ucsd.edu), [https://www.ocean-ops.org](https://www.ocean-ops.org)).

```bibtex
@article{argo2000,
  title={Argo: The global array of profiling floats},
  author={Roemmich, Dean and others},
  journal={Observing the Oceans in the 21st Century},
  year={2000}
}
```

---

## 📄 License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
