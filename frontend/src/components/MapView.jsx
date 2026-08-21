import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline } from 'react-leaflet'
import { getMapData } from '../api/client.js'
import TrajectoryPredictionLayer from './TrajectoryPredictionLayer.jsx'

const CENTER = [10.0, 72.0]
const ZOOM = 4

export default function MapView({ geojson }) {
  const [mapData, setMapData] = useState(null)

  useEffect(() => {
    if (!geojson) {
      getMapData().then(setMapData).catch(() => {})
    } else {
      setMapData(geojson)
    }
  }, [geojson])

  const features = mapData?.features || []

  return (
    <MapContainer center={CENTER} zoom={ZOOM} style={{ width: '100%', height: '100%' }}>
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
            key={i}
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
              <strong>WMO: {p.wmo_id}</strong><br />
              {p.platform_type && <span>Type: {p.platform_type}<br /></span>}
              {p.dac && <span>DAC: {p.dac}<br /></span>}
              {isBgc && <span className="bgc-badge">BGC</span>}
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
  )
}
