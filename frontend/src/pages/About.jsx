import React from 'react'
import { Link } from 'react-router-dom'
import { Waves, ExternalLink, Database, Cpu, Globe, BarChart2, Mic, Eye, FlaskConical } from 'lucide-react'

export default function About() {
  return (
    <div className="about-page">
      <nav className="topnav">
        <Link to="/" className="nav-logo">
          <Waves size={20} />
          <span>FloatChat</span>
        </Link>
        <div className="nav-links">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/dashboard" className="nav-link">Dashboard</Link>
        </div>
      </nav>

      <main className="about-content">
        <h1>About FloatChat</h1>
        <p className="about-lead">
          FloatChat is a RAG-powered conversational intelligence platform that makes ARGO ocean float data
          accessible to everyone — from school students and journalists to physical oceanographers.
        </p>

        <section>
          <h2>The ARGO Programme</h2>
          <p>
            The international Argo programme maintains over 4,000 autonomous profiling floats worldwide.
            Each float drifts at ~1000m depth, ascending every 10 days to profile temperature and salinity
            from 2000m to the surface. India's contribution through INCOIS covers the Indian Ocean,
            Arabian Sea, and Bay of Bengal — critical regions for monsoon and climate research.
          </p>
        </section>

        <section>
          <h2>Technology Stack</h2>
          <ul>
            <li><strong>Backend</strong>: FastAPI, SQLAlchemy, SQLite (PostgreSQL/PostGIS production-ready)</li>
            <li><strong>LLM / RAG</strong>: Groq (Llama 3.3 70B) with ChromaDB vector store for schema-grounded NL2SQL</li>
            <li><strong>Embeddings</strong>: SentenceTransformers (all-MiniLM-L6-v2) for semantic schema retrieval</li>
            <li><strong>Data Pipeline</strong>: argopy, xarray, NetCDF4 for ARGO float data ingestion</li>
            <li><strong>ML</strong>: scikit-learn (trajectory prediction), scipy (anomaly z-scores)</li>
            <li><strong>Voice</strong>: OpenAI Whisper for speech-to-text input</li>
            <li><strong>Frontend</strong>: React 18 + Vite, Leaflet.js (maps), Plotly.js (charts)</li>
          </ul>
        </section>

        <section>
          <h2>7 Unique Selling Points</h2>
          <ol>
            <li><strong>Anomaly & Change Narration</strong> — z-score analysis detects temperature/salinity anomalies and generates narratives</li>
            <li><strong>Multilingual Support</strong> — English, Hindi, Tamil, Bengali with automatic language detection</li>
            <li><strong>Trajectory Prediction</strong> — ML model predicts next float surfacing location with confidence scores</li>
            <li><strong>Voice Input</strong> — Speak your ocean data queries via Whisper STT</li>
            <li><strong>Full Explainability</strong> — See the SQL, routing decision, and RAG context behind every answer</li>
            <li><strong>Explorer + Researcher Modes</strong> — Plain language for citizens, raw data & QC flags for scientists</li>
            <li><strong>BGC-Argo Integration</strong> — Dissolved oxygen, chlorophyll, pH, nitrate from biogeochemical floats</li>
          </ol>
        </section>

        <section>
          <h2>Architecture</h2>
          <p>
            User questions flow through a multi-stage pipeline: language detection → translation →
            NL2SQL routing (15 templates + LLM fallback) → query execution → visualization shaping →
            LLM summary generation → translation back to user language. The system uses a vector store
            (ChromaDB) containing embedded database schema documentation to ground the LLM's SQL
            generation, ensuring accurate and safe queries.
          </p>
        </section>

        <div className="about-links">
          <a href="https://argo.ucsd.edu" target="_blank" rel="noopener noreferrer" className="btn btn-outline">
            <ExternalLink size={15} /> Argo Programme
          </a>
          <a href="https://incois.gov.in" target="_blank" rel="noopener noreferrer" className="btn btn-outline">
            <ExternalLink size={15} /> INCOIS
          </a>
          <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer" className="btn btn-outline">
            <ExternalLink size={15} /> Groq (Free LLM API)
          </a>
        </div>
      </main>
    </div>
  )
}
