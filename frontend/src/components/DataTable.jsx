import React from 'react'
import { Database } from 'lucide-react'

/**
 * DataTable — Researcher mode tabular data display.
 * Renders rows with QC flag color-coding and sticky headers.
 */
export default function DataTable({ rows }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="no-data">
        <Database size={32} />
        <span>No tabular data available</span>
      </div>
    )
  }

  const columns = Object.keys(rows[0])

  // QC flag color coding
  const qcClass = (col, value) => {
    if (!col.endsWith('_qc') || value == null) return ''
    const v = String(value)
    if (v === '1' || v === '2') return 'qc-good'
    if (v === '3') return 'qc-warn'
    if (v === '4') return 'qc-bad'
    return ''
  }

  // Format cell values
  const formatCell = (col, value) => {
    if (value == null || value === '') return '—'
    if (typeof value === 'number') {
      if (col.includes('lat') || col.includes('lon')) return value.toFixed(4)
      if (Number.isInteger(value)) return value.toString()
      return value.toFixed(3)
    }
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    return String(value)
  }

  return (
    <div className="data-table-wrap" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col.replace(/_/g, ' ')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={col} className={qcClass(col, row[col])}>
                    {formatCell(col, row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-info">
        {rows.length} row{rows.length !== 1 ? 's' : ''} • {columns.length} columns
      </div>
    </div>
  )
}
