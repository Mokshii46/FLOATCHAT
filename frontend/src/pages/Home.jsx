import React from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Waves, MessageSquare, Map, BarChart2, Globe } from 'lucide-react'

export default function Home() {
  const { t } = useTranslation()

  return (
    <div className="home-page">
      {/* Hero */}
      <header className="hero">
        <div className="hero-glow" />
        <div className="hero-content">
          <div className="hero-badge">
            <Waves size={16} />
            <span>SIH 2025 — Ocean Intelligence</span>
          </div>
          <h1 className="hero-title">FloatChat</h1>
          <p className="hero-subtitle">{t('tagline')}</p>
          <div className="hero-actions">
            <Link to="/dashboard" className="btn btn-primary">
              <MessageSquare size={18} />
              Start Exploring
            </Link>
            <Link to="/about" className="btn btn-outline">
              Learn More
            </Link>
          </div>
        </div>
      </header>

      {/* Features */}
      <section className="features">
        <h2 className="section-title">What FloatChat Can Do</h2>
        <div className="feature-grid">
          {[
            { icon: <MessageSquare size={28} />, title: 'Conversational Queries', desc: 'Ask about ocean data in plain language — no SQL needed.' },
            { icon: <Map size={28} />, title: 'Live Float Tracking', desc: 'See all ARGO floats on an interactive map with trajectory predictions.' },
            { icon: <BarChart2 size={28} />, title: 'Deep Analysis', desc: 'Temperature, salinity, oxygen, chlorophyll — depth profiles and time trends.' },
            { icon: <Globe size={28} />, title: 'Multilingual', desc: 'Works in English, Hindi, Tamil, Bengali, and more.' },
          ].map((f) => (
            <div key={f.title} className="feature-card">
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* USP chips */}
      <section className="usp-section">
        <h2 className="section-title">7 Unique Capabilities</h2>
        <div className="usp-chips">
          {['Anomaly Detection', 'Multilingual', 'Trajectory Prediction', 'Voice Input',
            'Explainability', 'Citizen & Researcher Modes', 'BGC-Argo Integration'].map((u) => (
            <span key={u} className="usp-chip">{u}</span>
          ))}
        </div>
      </section>
    </div>
  )
}
