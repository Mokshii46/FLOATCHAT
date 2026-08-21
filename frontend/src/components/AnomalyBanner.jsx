import React from 'react'
import { AlertTriangle, AlertOctagon } from 'lucide-react'

/**
 * USP 1 — Displays an anomaly warning/critical banner below the chat message.
 */
export default function AnomalyBanner({ anomaly }) {
  if (!anomaly || anomaly.severity === 'normal') return null

  const isCritical = anomaly.severity === 'critical'

  return (
    <div className={`anomaly-banner ${isCritical ? 'critical' : 'warning'}`}>
      <div className="anomaly-icon">
        {isCritical ? <AlertOctagon size={18} /> : <AlertTriangle size={18} />}
      </div>
      <div className="anomaly-body">
        <span className="anomaly-label">
          {isCritical ? '⚠️ Significant Anomaly Detected' : '⚡ Anomaly Detected'}
        </span>
        <p className="anomaly-text">{anomaly.narrative}</p>
        {anomaly.z_score !== undefined && (
          <span className="anomaly-zscore">z-score: {anomaly.z_score.toFixed(2)}</span>
        )}
      </div>
    </div>
  )
}
