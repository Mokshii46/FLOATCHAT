import React from 'react'
import { Link } from 'react-router-dom'
import { Waves, ExternalLink, HelpCircle, MessageSquare, Compass, FlaskConical } from 'lucide-react'

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
          FloatChat lets you explore ocean data collected by thousands of robotic floats around the
          world — just by asking questions in plain language. No coding, no databases, no jargon required.
        </p>

        <section>
          <h2>What Are ARGO Floats?</h2>
          <p>
            ARGO floats are autonomous instruments — roughly the size of a fire extinguisher — that
            drift through the ocean collecting data. Over 4,000 of them are active worldwide, maintained
            by more than 30 nations as part of the international Argo programme.
          </p>
          <p style={{ marginTop: '0.75rem' }}>
            Each float follows a 10-day cycle: it sinks to about 1,000 metres, drifts with deep ocean
            currents, then descends further to 2,000 metres before rising slowly to the surface. As it
            ascends, it measures temperature and salinity at every depth. Once at the surface, it transmits
            all its data via satellite before sinking again. Some advanced "BGC" (biogeochemical) floats
            also measure dissolved oxygen, chlorophyll, pH, and nitrate — giving us a window into ocean
            health and marine ecosystems.
          </p>
          <p style={{ marginTop: '0.75rem' }}>
            India contributes floats through INCOIS (Indian National Centre for Ocean Information Services),
            covering the Indian Ocean, Arabian Sea, and Bay of Bengal — regions critical for understanding
            the monsoon and climate variability.
          </p>
        </section>

        <section>
          <h2>How to Read a Profile</h2>
          <p>
            When you ask about a float's data, FloatChat often shows a <strong>depth profile</strong> — a
            chart where the vertical axis is pressure (depth) increasing downward, and the horizontal axis
            is a measurement like temperature or salinity. Think of it as a cross-section of the ocean:
            the top of the chart is the surface and the bottom is deep water.
          </p>
          <p style={{ marginTop: '0.75rem' }}>
            A typical temperature profile starts warm at the surface (~28°C in tropical waters), drops
            sharply through the thermocline (the transition layer), and levels off to cold temperatures
            (~2–4°C) in the deep ocean. Changes in this shape over time can reveal warming trends,
            shifts in ocean circulation, or unusual events.
          </p>
        </section>

        <section>
          <h2>Asking Good Questions</h2>
          <p>
            FloatChat works best with clear, specific questions. Here are some examples you can try
            on the <Link to="/dashboard" style={{ color: 'var(--accent-bright)' }}>Dashboard</Link>:
          </p>
          <ul style={{ marginTop: '0.75rem' }}>
            <li><strong>"What is the average temperature in the Arabian Sea this year?"</strong> — Returns a time-series chart of monthly averages.</li>
            <li><strong>"Show me all active BGC floats on the map."</strong> — Displays float locations with BGC sensors highlighted.</li>
            <li><strong>"Chlorophyll profile for float 6904160."</strong> — Shows a depth profile of chlorophyll concentration.</li>
            <li><strong>"Is there anything unusual about temperatures in the Bay of Bengal recently?"</strong> — Triggers anomaly detection and shows any significant deviations.</li>
          </ul>
          <p style={{ marginTop: '0.75rem' }}>
            You can also ask in Hindi, Tamil, Bengali, and other Indian languages — FloatChat will
            detect your language and respond in it.
          </p>
        </section>

        <section>
          <h2>Explorer vs Researcher Mode</h2>
          <div style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
            <div style={{ flex: '1 1 280px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Compass size={18} style={{ color: 'var(--accent-bright)' }} />
                <strong>Explorer Mode</strong>
              </div>
              <p>
                Designed for students, journalists, and anyone curious about the ocean. You'll get
                friendly summaries in plain language, visual charts, and guided prompt suggestions.
                Technical details like SQL queries and quality control flags stay hidden so you can
                focus on understanding the data.
              </p>
            </div>
            <div style={{ flex: '1 1 280px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <FlaskConical size={18} style={{ color: 'var(--researcher)' }} />
                <strong>Researcher Mode</strong>
              </div>
              <p>
                Built for oceanographers and scientists. You'll see the exact SQL query used to
                fetch data, quality control (QC) flags on each measurement, raw data tables with
                full numeric precision, and detailed technical summaries. Everything you need to
                verify and cite the results.
              </p>
            </div>
          </div>
          <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Toggle between modes using the switch in the top navigation bar on the Dashboard.
          </p>
        </section>

        <section>
          <h2>Frequently Asked Questions</h2>

          <div className="faq-item">
            <div className="faq-q">
              <HelpCircle size={16} style={{ color: 'var(--accent-bright)', flexShrink: 0, marginTop: '2px' }} />
              <strong>How current is the data?</strong>
            </div>
            <p>
              FloatChat's database is refreshed regularly from the global ARGO data centres. Most
              float observations are available within 24 hours of transmission. However, some data
              undergoes delayed-mode quality control that can take months — so the very latest
              readings may carry preliminary QC flags.
            </p>
          </div>

          <div className="faq-item">
            <div className="faq-q">
              <HelpCircle size={16} style={{ color: 'var(--accent-bright)', flexShrink: 0, marginTop: '2px' }} />
              <strong>What does the anomaly badge mean?</strong>
            </div>
            <p>
              When FloatChat detects that a recent measurement is statistically unusual compared to
              the historical average for that region, it shows a warning badge with a z-score. A
              z-score above 2.0 means the value is more than two standard deviations from the mean —
              worth investigating, though not necessarily alarming.
            </p>
          </div>

          <div className="faq-item">
            <div className="faq-q">
              <HelpCircle size={16} style={{ color: 'var(--accent-bright)', flexShrink: 0, marginTop: '2px' }} />
              <strong>What are the colored dots on the map?</strong>
            </div>
            <p>
              Indigo dots are standard Argo floats (measuring temperature and salinity). Larger cyan
              dots are BGC-Argo floats with additional biogeochemical sensors. Click any dot to see
              its WMO ID and ask questions about it directly.
            </p>
          </div>

          <div className="faq-item">
            <div className="faq-q">
              <HelpCircle size={16} style={{ color: 'var(--accent-bright)', flexShrink: 0, marginTop: '2px' }} />
              <strong>Can I download the data?</strong>
            </div>
            <p>
              Yes — after any query, click the "Export CSV" button below the chat input to download
              the raw data as a CSV file. You can also access the complete Argo dataset directly
              from the Argo Data Management site.
            </p>
          </div>
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
