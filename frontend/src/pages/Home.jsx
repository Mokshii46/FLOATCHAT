import React from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Waves, MessageSquare, Map, BarChart2, Globe, Compass, FlaskConical, ArrowRight, Anchor } from 'lucide-react'

export default function Home() {
  const { t } = useTranslation()

  return (
    <div className="home-page">
      {/* Animated ocean background */}
      <div className="ocean-bg" />

      <div className="home-content">
        {/* Navigation */}
        <nav className="home-nav">
          <Link to="/" className="nav-logo">
            <Waves size={22} />
            <span>FloatChat</span>
          </Link>
          <div className="nav-links">
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/about" className="nav-link">About</Link>
          </div>
        </nav>

        {/* Hero */}
        <header className="hero">
          <div className="hero-badge">
            <Anchor size={14} />
            <span>Ocean Intelligence Platform</span>
          </div>
          <h1 className="hero-title">FloatChat</h1>
          <p className="hero-subtitle">
            Explore ARGO ocean float data through natural conversation. Ask about sea temperatures,
            salinity, float trajectories, and biogeochemical data — in plain language or with precision.
          </p>
          <div className="hero-actions">
            <Link to="/dashboard" className="btn btn-primary" id="hero-cta-explore">
              <Compass size={18} />
              Start Exploring
              <ArrowRight size={16} />
            </Link>
            <Link to="/about" className="btn btn-outline" id="hero-cta-learn">
              Learn More
            </Link>
          </div>
        </header>

        {/* Stats */}
        <div className="stats-row">
          {[
            { value: '4,000+', label: 'Active Floats Worldwide' },
            { value: '30+', label: 'Contributing Nations' },
            { value: '2,000m', label: 'Standard Profiling Depth' },
            { value: '6', label: 'BGC Parameters Tracked' },
          ].map((s) => (
            <div key={s.label} className="stat-item">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Features */}
        <section className="features">
          <h2 className="section-title">What FloatChat Can Do</h2>
          <div className="feature-grid">
            {[
              { icon: <MessageSquare size={24} />, title: 'Conversational Queries', desc: 'Ask about ocean data in plain language. Our AI converts your questions into precise database queries automatically.' },
              { icon: <Map size={24} />, title: 'Live Float Tracking', desc: 'Visualize all ARGO floats on an interactive map with ML-powered trajectory predictions for next surfacing.' },
              { icon: <BarChart2 size={24} />, title: 'Deep Analysis', desc: 'Temperature, salinity, dissolved oxygen, chlorophyll — depth profiles and monthly time series at your fingertips.' },
              { icon: <Globe size={24} />, title: 'Multilingual Support', desc: 'Works in English, Hindi, Tamil, Bengali and more. Ask in your language, get answers in your language.' },
            ].map((f) => (
              <div key={f.title} className="feature-card">
                <div className="feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Two Modes */}
        <section className="features" style={{ paddingTop: 0 }}>
          <h2 className="section-title">Two Modes, One Platform</h2>
          <div className="feature-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
            <div className="feature-card">
              <div className="feature-icon" style={{ background: 'rgba(13,148,136,0.12)' }}>
                <Compass size={24} />
              </div>
              <h3>Explorer Mode</h3>
              <p>Designed for students, journalists, and curious minds. Simple language, guided prompts, and visual-first results. No jargon, no confusion.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ background: 'rgba(245,158,11,0.12)', color: '#f59e0b' }}>
                <FlaskConical size={24} />
              </div>
              <h3>Researcher Mode</h3>
              <p>Built for oceanographers and scientists. Raw data tables, QC flags visible, SQL queries exposed, and full numeric precision in every response.</p>
            </div>
          </div>
        </section>

        {/* USP chips */}
        <section className="usp-section">
          <h2 className="section-title">6 Unique Capabilities</h2>
          <div className="usp-chips">
            {['🔍 Anomaly Detection', '🎯 Trajectory Prediction', '🎤 Voice Input',
              '📊 Explainability', '👥 Dual Modes', '🧬 BGC-Argo Integration'].map((u) => (
              <span key={u} className="usp-chip">{u}</span>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="home-footer">
          <p>FloatChat Powered by ARGO Programme & INCOIS data</p>
        </footer>
      </div>
    </div>
  )
}
