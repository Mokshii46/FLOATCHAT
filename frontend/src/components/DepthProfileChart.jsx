import React from 'react'
import Plot from 'react-plotly.js'

/**
 * Renders a Plotly horizontal depth-profile chart (parameter vs pressure).
 * Pressure increases downward (y-axis reversed).
 */
export default function DepthProfileChart({ data }) {
  if (!data || !data.traces || data.traces.length === 0) {
    return <div className="no-data">No depth profile data available.</div>
  }

  const traces = data.traces.map((t) => ({
    name: t.name,
    x: t.x,
    y: t.y,
    mode: 'lines+markers',
    type: 'scatter',
    marker: { size: 4 },
    line: { width: 2 },
  }))

  const xTitle = data.traces[0]?.param || 'Value'

  return (
    <Plot
      data={traces}
      layout={{
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e8f0', family: 'Inter, sans-serif', size: 12 },
        margin: { t: 30, r: 20, b: 50, l: 60 },
        xaxis: { title: xTitle, gridcolor: '#334155' },
        yaxis: {
          title: 'Pressure (dbar)',
          autorange: 'reversed',
          gridcolor: '#334155',
        },
        legend: { bgcolor: 'rgba(0,0,0,0)', x: 1.02 },
        showlegend: traces.length > 1,
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: '100%', height: '100%' }}
    />
  )
}
