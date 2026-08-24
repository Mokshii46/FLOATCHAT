import React from 'react'
import { Thermometer, Droplets, Wind, Waves, Beaker, Activity } from 'lucide-react'

const PARAM_CONFIG = {
  temperature: { icon: Thermometer, unit: '°C', color: '#ef4444', label: 'Temperature' },
  avg_temp_c: { icon: Thermometer, unit: '°C', color: '#ef4444', label: 'Avg Temperature' },
  avg_temp: { icon: Thermometer, unit: '°C', color: '#ef4444', label: 'Avg Temperature' },
  salinity: { icon: Droplets, unit: 'PSU', color: '#3b82f6', label: 'Salinity' },
  avg_salinity_psu: { icon: Droplets, unit: 'PSU', color: '#3b82f6', label: 'Avg Salinity' },
  dissolved_oxygen: { icon: Wind, unit: 'µmol/kg', color: '#22c55e', label: 'Dissolved Oxygen' },
  avg_oxygen_umolkg: { icon: Wind, unit: 'µmol/kg', color: '#22c55e', label: 'Avg Dissolved Oxygen' },
  chlorophyll: { icon: Beaker, unit: 'mg/m³', color: '#10b981', label: 'Chlorophyll-a' },
  ph: { icon: Activity, unit: '', color: '#8b5cf6', label: 'pH' },
  nitrate: { icon: Beaker, unit: 'µmol/kg', color: '#f59e0b', label: 'Nitrate' },
  pressure: { icon: Waves, unit: 'dbar', color: '#06b6d4', label: 'Pressure' },
}

/**
 * Visually appealing stat card for single-value query results.
 * Shows a large number with unit, parameter icon, and optional context labels.
 */
export default function StatCard({ data }) {
  if (!data) return null

  const { value, param, unit, label, context } = data

  const config = PARAM_CONFIG[param] || { icon: Activity, unit: unit || '', color: '#6366f1', label: param || 'Value' }
  const Icon = config.icon
  const displayUnit = unit || config.unit
  const displayLabel = label || config.label
  const displayValue = typeof value === 'number' ? value.toFixed(2) : value

  return (
    <div className="stat-card">
      <div className="stat-card-icon" style={{ background: `${config.color}15`, color: config.color }}>
        <Icon size={28} />
      </div>
      <div className="stat-card-body">
        <div className="stat-card-value" style={{ color: config.color }}>
          {displayValue}
          <span className="stat-card-unit">{displayUnit}</span>
        </div>
        <div className="stat-card-label">{displayLabel}</div>
        {context && <div className="stat-card-context">{context}</div>}
      </div>
    </div>
  )
}
