import React, { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Waves, Globe, BarChart3, Database, HelpCircle, ShieldCheck, Compass } from 'lucide-react'
import ChatPanel from '../components/ChatPanel.jsx'
import MapView from '../components/MapView.jsx'
import DepthProfileChart from '../components/DepthProfileChart.jsx'
import TimeSeriesChart from '../components/TimeSeriesChart.jsx'
import DataTable from '../components/DataTable.jsx'
import StatCard from '../components/StatCard.jsx'
import ModeToggle from '../components/ModeToggle.jsx'
import GuidedTour from '../components/GuidedTour.jsx'
import { useChat } from '../hooks/useChat.js'

export default function Dashboard() {
  const { messages, mode, mapResetKey } = useChat()
  const [activeTab, setActiveTab] = useState('map') // 'map' | 'chart' | 'table'
  const [showTour, setShowTour] = useState(false)

  // Find the most recent assistant message with viz data
  const latestViz = [...messages]
    .reverse()
    .find((m) => m.role === 'assistant' && m.viz)?.viz

  // Extract raw rows available for data table
  const rawRows = latestViz?.raw_rows || latestViz?.data?.rows || []
  const hasTableData = rawRows && rawRows.length > 0

  const hasChartViz =
    latestViz &&
    ['timeseries', 'depth_profile', 'stat_card'].includes(latestViz.viz_type)

  const chartLabel = useMemo(() => {
    if (!latestViz) return 'Chart'
    if (latestViz.viz_type === 'timeseries') return 'Time-Series Trend'
    if (latestViz.viz_type === 'depth_profile') return 'Depth Profile'
    if (latestViz.viz_type === 'stat_card') return 'Stat Card'
    return 'Chart'
  }, [latestViz])

  // Extract GeoJSON if present for highlighting on map
  const mapGeojson = latestViz?.viz_type === 'map' ? latestViz.data : null

  // Whenever a new query arrives, switch to appropriate viz tab automatically
  useEffect(() => {
    if (!latestViz) {
      setActiveTab('map')
    } else if (latestViz.viz_type === 'map') {
      setActiveTab('map')
    } else if (['timeseries', 'depth_profile', 'stat_card'].includes(latestViz.viz_type)) {
      setActiveTab('chart')
    } else if (latestViz.viz_type === 'table') {
      setActiveTab(mode === 'researcher' ? 'table' : 'map')
    }
  }, [latestViz, mode])

  const renderVizContent = () => {
    if (activeTab === 'map') {
      return <MapView geojson={mapGeojson} resetKey={mapResetKey} />
    }

    if (activeTab === 'table' && hasTableData) {
      return <DataTable rows={rawRows} />
    }

    if (activeTab === 'chart' && latestViz) {
      switch (latestViz.viz_type) {
        case 'depth_profile':
          return <DepthProfileChart data={latestViz.data} />
        case 'timeseries':
          return <TimeSeriesChart data={latestViz.data} />
        case 'stat_card':
          return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '2rem' }}>
              <StatCard data={latestViz.data} />
            </div>
          )
        case 'map':
          return <MapView geojson={latestViz.data} resetKey={mapResetKey} />
        default:
          return <MapView resetKey={mapResetKey} />
      }
    }

    // Default fallback to Map
    return <MapView geojson={mapGeojson} resetKey={mapResetKey} />
  }

  return (
    <div className="dashboard">
      <GuidedTour isOpen={showTour} onClose={() => setShowTour(false)} />

      {/* Top nav */}
      <nav className="topnav">
        <Link to="/" className="nav-logo">
          <Waves size={20} />
          <span>FloatChat</span>
        </Link>
        <ModeToggle />
        <div className="nav-links">
          <button
            className="tour-nav-btn"
            onClick={() => setShowTour(true)}
            title="Take a quick guided tour"
          >
            <HelpCircle size={14} />
            <span>Tour</span>
          </button>
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/about" className="nav-link">About</Link>
        </div>
      </nav>

      {/* Main layout: chat | viz */}
      <main className="dashboard-main">
        <aside className="chat-sidebar">
          <ChatPanel />
        </aside>
        <section className="viz-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Universal Viz Navigation Bar (Map / Chart / Table) */}
          <div className="viz-control-bar">
            <div className="viz-tabs">
              <button
                className={`viz-tab-btn ${activeTab === 'map' ? 'active' : ''}`}
                onClick={() => setActiveTab('map')}
                title="View interactive 360° global float fleet"
              >
                <Globe size={14} />
                <span>Map View</span>
              </button>

              {hasChartViz && (
                <button
                  className={`viz-tab-btn ${activeTab === 'chart' ? 'active' : ''}`}
                  onClick={() => setActiveTab('chart')}
                  title="View graphical chart visualization"
                >
                  <BarChart3 size={14} />
                  <span>Graphical Viz ({chartLabel})</span>
                </button>
              )}

              {mode === 'researcher' && hasTableData && (
                <button
                  className={`viz-tab-btn ${activeTab === 'table' ? 'active' : ''}`}
                  onClick={() => setActiveTab('table')}
                  title="View raw observation rows with QC flags"
                >
                  <Database size={14} />
                  <span>Raw Data Table ({rawRows.length} rows)</span>
                </button>
              )}
            </div>

            <div className="viz-bar-info">
              {mode === 'researcher' ? (
                <div className="researcher-info-pill">
                  <ShieldCheck size={13} color="#10b981" />
                  <span>QC Quality Control Active</span>
                </div>
              ) : (
                <div className="explorer-info-pill">
                  <Compass size={13} color="#38bdf8" />
                  <span>Interactive 360° Float Fleet</span>
                </div>
              )}
            </div>
          </div>

          {/* Main Visualizer Content Area */}
          <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
            {renderVizContent()}
          </div>
        </section>
      </main>
    </div>
  )
}
