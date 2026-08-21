import React from 'react'
import { Polyline, CircleMarker, Popup } from 'react-leaflet'

/**
 * USP 3 — Renders a dashed line from the float's current position to its
 * predicted next surfacing point, with a confidence-coloured marker.
 */
export default function TrajectoryPredictionLayer({
  currentLat, currentLon, predLat, predLon, confidence,
}) {
  if (!predLat || !predLon) return null

  const opacity = confidence ? Math.max(0.3, confidence) : 0.5
  const color = confidence > 0.7 ? '#22c55e' : confidence > 0.5 ? '#f59e0b' : '#ef4444'

  return (
    <>
      <Polyline
        positions={[
          [currentLat, currentLon],
          [predLat, predLon],
        ]}
        pathOptions={{ color, dashArray: '6 4', weight: 2, opacity }}
      />
      <CircleMarker
        center={[predLat, predLon]}
        radius={5}
        pathOptions={{ color, fillColor: color, fillOpacity: 0.6, weight: 2, dashArray: '4 2' }}
      >
        <Popup>
          <strong>Predicted next surfacing</strong><br />
          Lat: {predLat.toFixed(3)}, Lon: {predLon.toFixed(3)}<br />
          Confidence: {confidence ? `${(confidence * 100).toFixed(0)}%` : 'N/A'}
        </Popup>
      </CircleMarker>
    </>
  )
}
