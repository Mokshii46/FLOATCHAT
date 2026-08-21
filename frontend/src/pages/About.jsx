import React from 'react'
import { Link } from 'react-router-dom'
import { Waves, Github, ExternalLink } from 'lucide-react'

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
          FloatChat is a RAG-powered conversational interface that makes ARGO ocean float data
          accessible to everyone — from school students to oceanographers.
        </p>

        <section>
          <h2>The ARGO Programme</h2>
          <p>
            The Argo programme maintains over 4,000 autonomous floats worldwide that profile
            the ocean from 0 to 2000 meters depth every 10 days. India's contribution through
            INCOIS covers the Indian Ocean, Arabian Sea, and Bay of Bengal.
          </p>
        </section>

        <section>
          <h2>Technology Stack</h2>
          <ul>
            <li><strong>Backend</strong>: FastAPI, SQLAlchemy, PostGIS, ChromaDB</li>
            <li><strong>LLM</strong>: Anthropic Claude (NL2SQL + summaries + translation)</li>
            <li><strong>Data</strong>: argopy, xarray, NetCDF4</li>
            <li><strong>ML</strong>: scikit-learn (trajectory), scipy (anomaly)</li>
            <li><strong>Voice</strong>: OpenAI Whisper STT</li>
            <li><strong>Frontend</strong>: React + Vite, Leaflet, Plotly</li>
          </ul>
        </section>

        <section>
          <h2>7 Unique Selling Points</h2>
          <ol>
            <li>Anomaly / change narration with z-score analysis</li>
            <li>Multilingual support (English, Hindi, Tamil, Bengali…)</li>
            <li>Trajectory prediction for next float surfacing</li>
            <li>Voice input via Whisper STT</li>
            <li>Full query explainability — see the SQL behind every answer</li>
            <li>Citizen mode (plain language) vs Researcher mode (raw data)</li>
            <li>BGC-Argo integration (O₂, Chlorophyll, pH, Nitrate)</li>
          </ol>
        </section>

        <div className="about-links">
          <a href="https://argo.ucsd.edu" target="_blank" rel="noopener noreferrer" className="btn btn-outline">
            <ExternalLink size={15} /> Argo Programme
          </a>
          <a href="https://incois.gov.in" target="_blank" rel="noopener noreferrer" className="btn btn-outline">
            <ExternalLink size={15} /> INCOIS
          </a>
        </div>
      </main>
    </div>
  )
}
