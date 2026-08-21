import React from 'react'
import Plot from 'react-plotly.js'

/**
 * Plotly line chart for time-series data (monthly means, trends, anomalies).
 */
export default function TimeSeriesChart({ data }) {
  if (!data || !data.series || data.series.length === 0) {
    return <div className="no-data">No time-series data available.</div>
  }

  const traces = data.series.map((s, i) => ({
    name: s.name,
    x: s.x,
    y: s.y,
    type: 'scatter',
    mode: 'lines+markers',
    marker: { size: 5 },
    line: { width: 2 },
  }))

  return (
    <Plot
      data={traces}
      layout={{
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e8f0', family: 'Inter, sans-serif', size: 12 },
        margin: { t: 30, r: 20, b: 60, l: 60 },
        xaxis: { title: 'Date', gridcolor: '#334155' },
        yaxis: { gridcolor: '#334155' },
        legend: { bgcolor: 'rgba(0,0,0,0)' },
        showlegend: traces.length > 1,
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: '100%', height: '100%' }}
    />
  )
}
