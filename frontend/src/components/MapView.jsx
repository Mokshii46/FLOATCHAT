import React, { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import { getMapData } from '../api/client.js'
import { useChat } from '../hooks/useChat.js'
import TrajectoryPredictionLayer from './TrajectoryPredictionLayer.jsx'
import { Loader2, MessageSquare, MapPin } from 'lucide-react'

const CENTER = [10.0, 72.0]
const ZOOM = 4

/**
 * Inner component that reacts to geojson/reset changes without remounting MapContainer.
 * Uses useMap() hook to imperatively update the map.
 */
function MapController({ resetKey }) {
  const map = useMap()

  useEffect(() => {
    if (resetKey > 0) {
      map.flyTo(CENTER, ZOOM, { duration: 0.8 })
    }
  }, [resetKey, map])

  return null
}

export default function MapView({ geojson, resetKey = 0 }) {
  const [mapData, setMapData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const { sendMessage } = useChat()

  useEffect(() => {
    if (!geojson) {
      setIsLoading(true)
      getMapData()
        .then(setMapData)
        .catch(() => {})
        .finally(() => setIsLoading(false))
    } else {
      setMapData(geojson)
      setIsLoading(false)
    }
  }, [geojson])

  const features = mapData?.features || []

  const handleAskAbout = useCallback((wmoId) => {
    sendMessage(`Tell me about float ${wmoId}`)
  }, [sendMessage])

  const handleAskLocation = useCallback((lat, lon) => {
    sendMessage(`What is the recent ocean data near latitude ${lat.toFixed(2)}, longitude ${lon.toFixed(2)}?`)
  }, [sendMessage])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Loading overlay */}
      {isLoading && (
        <div className="map-loading-overlay">
          <Loader2 size={28} className="spin" />
          <span>Loading float data…</span>
        </div>
      )}

      <MapContainer
        center={CENTER}
        zoom={ZOOM}
        minZoom={2}
        maxZoom={18}
        scrollWheelZoom={true}
        zoomControl={true}
        style={{ width: '100%', height: '100%' }}
      >
        <MapController resetKey={resetKey} />
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
        />

        {features.map((f, i) => {
          const [lon, lat] = f.geometry.coordinates
          const p = f.properties
          const isBgc = p.is_bgc

          return (
            <CircleMarker
              key={`${p.wmo_id || i}-${i}`}
              center={[lat, lon]}
              radius={isBgc ? 8 : 6}
              pathOptions={{
                color: isBgc ? '#06b6d4' : '#6366f1',
                fillColor: isBgc ? '#06b6d4' : '#6366f1',
                fillOpacity: 0.8,
                weight: 1.5,
              }}
            >
              <Popup>
                <div className="float-popup">
                  <strong>WMO: {p.wmo_id}</strong><br />
                  {p.platform_type && <span>Type: {p.platform_type}<br /></span>}
                  {p.dac && <span>DAC: {p.dac}<br /></span>}
                  {isBgc && <span className="bgc-badge">BGC</span>}
                  <div className="popup-actions">
                    <button
                      className="popup-action-btn"
                      onClick={(e) => { e.stopPropagation(); handleAskAbout(p.wmo_id) }}
                    >
                      <MessageSquare size={12} />
                      Ask about this float
                    </button>
                    <button
                      className="popup-action-btn"
                      onClick={(e) => { e.stopPropagation(); handleAskLocation(lat, lon) }}
                    >
                      <MapPin size={12} />
                      Ask about this location
                    </button>
                  </div>
                </div>
              </Popup>

              {/* Prediction marker */}
              <TrajectoryPredictionLayer
                currentLat={lat}
                currentLon={lon}
                predLat={p.predicted_next_lat}
                predLon={p.predicted_next_lon}
                confidence={p.prediction_confidence}
              />
            </CircleMarker>
          )
        })}
      </MapContainer>

      {/* Empty state overlay */}
      {!isLoading && features.length === 0 && geojson && (
        <div className="map-empty-overlay">
          <MapPin size={24} />
          <span>No floats found for this query</span>
        </div>
      )}

      {/* Legend */}
      <div className="map-legend">
        <div className="legend-title">Float Types</div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#6366f1' }}></span>
          <span>Standard Argo</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot legend-dot-lg" style={{ background: '#06b6d4' }}></span>
          <span>BGC-Argo</span>
        </div>
      </div>
    </div>
  )
}
