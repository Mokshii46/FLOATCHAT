import React from 'react'
import { Polyline, CircleMarker, Popup } from 'react-leaflet'

/**
 * USP 3 — Renders a dashed trajectory drift line from the float's position to its
 * predicted next surfacing point with a confidence indicator.
 */
export default function TrajectoryPredictionLayer({
  currentLat,
  currentLon,
  predLat,
  predLon,
  confidence,
  zoom = 4,
}) {
  if (!predLat || !predLon) return null

  const color = confidence > 0.7 ? '#10b981' : confidence > 0.5 ? '#f59e0b' : '#38bdf8'
  const radius = zoom <= 3 ? 2.5 : zoom <= 5 ? 4.0 : 5.5

  return (
    <>
      <Polyline
        positions={[
          [currentLat, currentLon],
          [predLat, predLon],
        ]}
        pathOptions={{
          color,
          dashArray: '4 3',
          weight: 1.5,
          opacity: 0.7,
        }}
      />
      <CircleMarker
        center={[predLat, predLon]}
        radius={radius}
        pathOptions={{
          color,
          fillColor: color,
          fillOpacity: 0.7,
          weight: 1,
        }}
      >
        <Popup>
          <div className="float-popup">
            <strong>Predicted Next Surfacing</strong><br />
            <span>Lat: {predLat.toFixed(3)}, Lon: {predLon.toFixed(3)}</span><br />
            <span>Confidence: {confidence ? `${(confidence * 100).toFixed(0)}%` : 'N/A'}</span>
          </div>
        </Popup>
      </CircleMarker>
    </>
  )
}
