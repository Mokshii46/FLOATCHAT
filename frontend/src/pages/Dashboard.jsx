import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Waves } from 'lucide-react'
import ChatPanel from '../components/ChatPanel.jsx'
import MapView from '../components/MapView.jsx'
import DepthProfileChart from '../components/DepthProfileChart.jsx'
import TimeSeriesChart from '../components/TimeSeriesChart.jsx'
import ModeToggle from '../components/ModeToggle.jsx'
import { useChat } from '../hooks/useChat.js'

export default function Dashboard() {
  const { messages } = useChat()

  // Find the most recent assistant message with viz data
  const latestViz = [...messages]
    .reverse()
    .find((m) => m.role === 'assistant' && m.viz)?.viz

  const renderViz = () => {
    if (!latestViz) return <MapView />

    switch (latestViz.viz_type) {
      case 'map':
        return <MapView geojson={latestViz.data} />
      case 'depth_profile':
        return <DepthProfileChart data={latestViz.data} />
      case 'timeseries':
        return <TimeSeriesChart data={latestViz.data} />
      default:
        return <MapView />
    }
  }

  return (
    <div className="dashboard">
      {/* Top nav */}
      <nav className="topnav">
        <Link to="/" className="nav-logo">
          <Waves size={20} />
          <span>FloatChat</span>
        </Link>
        <ModeToggle />
        <div className="nav-links">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/about" className="nav-link">About</Link>
        </div>
      </nav>

      {/* Main layout: chat | viz */}
      <main className="dashboard-main">
        <aside className="chat-sidebar">
          <ChatPanel />
        </aside>
        <section className="viz-panel">
          {renderViz()}
        </section>
      </main>
    </div>
  )
}
