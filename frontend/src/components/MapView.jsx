import React, { useEffect, useState, useCallback, useMemo } from 'react'
import L from 'leaflet'
import { MapContainer, TileLayer, CircleMarker, Marker, Popup, useMap, useMapEvents } from 'react-leaflet'
import { getMapData } from '../api/client.js'
import { useChat } from '../hooks/useChat.js'
import { Loader2, MessageSquare, MapPin, Globe, Compass, Database, Activity, GitCompare, Star } from 'lucide-react'

const CENTER = [15.0, 30.0]
const DEFAULT_ZOOM = 3

// ── Multi-World Wrapping Offsets for Seamless 360° Infinite Scrolling ────
const WRAP_OFFSETS = [-720, -360, 0, 360, 720]

// Lock vertical scrolling strictly between polar extents (-85° to +85°)
const LAT_BOUNDS = [
  [-85.0, -Infinity],
  [85.0, Infinity],
]

// ── The 7 World Oceans & Key Regional Basins ────────────────────────────
const MAJOR_OCEANS = [
  { id: 'indian', name: 'Indian Ocean', lat: -14.0, lon: 75.0, type: 'ocean', desc: 'Core Indian Ocean ARGO Basin' },
  { id: 'arabian', name: 'Arabian Sea', lat: 16.5, lon: 64.0, type: 'sea', desc: 'Northern Indian Ocean (High Salinity & Oxygen Minimum Zone)' },
  { id: 'bengal', name: 'Bay of Bengal', lat: 14.5, lon: 88.5, type: 'sea', desc: 'Northeastern Indian Ocean (Monsoon & Low Salinity River Inflow)' },
  { id: 'n_atlantic', name: 'North Atlantic Ocean', lat: 30.0, lon: -40.0, type: 'ocean', desc: 'Atlantic Basin & Gulf Stream System' },
  { id: 's_atlantic', name: 'South Atlantic Ocean', lat: -20.0, lon: -18.0, type: 'ocean', desc: 'South Atlantic Subtropical Gyre' },
  { id: 'n_pacific', name: 'North Pacific Ocean', lat: 30.0, lon: 165.0, type: 'ocean', desc: 'Largest World Ocean Basin (Kuroshio & North Pacific Current)' },
  { id: 's_pacific', name: 'South Pacific Ocean', lat: -22.0, lon: -135.0, type: 'ocean', desc: 'South Pacific Subtropical Gyre' },
  { id: 'southern', name: 'Southern Ocean', lat: -58.0, lon: 70.0, type: 'ocean', desc: 'Antarctic Circumpolar Current & Deep Water Formation' },
  { id: 'arctic', name: 'Arctic Ocean', lat: 78.0, lon: 15.0, type: 'ocean', desc: 'Polar Sea Ice & Northernmost Ocean Basin' },
]

/**
 * Sync zoom state, handle reset, and fly to highlighted floats.
 */
function MapEventsController({ resetKey, onZoomChange, focusTarget }) {
  const map = useMap()

  useMapEvents({
    zoomend: () => {
      onZoomChange(map.getZoom())
    },
  })

  useEffect(() => {
    if (resetKey > 0) {
      map.flyTo(CENTER, DEFAULT_ZOOM, { duration: 0.8 })
      onZoomChange(DEFAULT_ZOOM)
    }
  }, [resetKey, map, onZoomChange])

  // Fly to focused float if a specific float query occurred
  useEffect(() => {
    if (focusTarget && focusTarget.lat != null && focusTarget.lon != null) {
      map.flyTo([focusTarget.lat, focusTarget.lon], Math.max(map.getZoom(), 4), {
        duration: 1.2,
      })
    }
  }, [focusTarget, map])

  return null
}

/**
 * Dynamic sizing based on zoom level to ensure clean visibility.
 */
function getFloatDotRadius(isBgc, isHighlighted, zoom) {
  let base
  if (zoom <= 2) base = isBgc ? 3.0 : 2.0
  else if (zoom === 3) base = isBgc ? 3.8 : 2.6
  else if (zoom === 4) base = isBgc ? 5.2 : 3.8
  else if (zoom === 5) base = isBgc ? 6.8 : 5.0
  else base = isBgc ? 8.5 : 6.5

  return isHighlighted ? base * 1.5 + 2 : base
}

function getFloatDotWeight(isHighlighted, zoom) {
  if (isHighlighted) return 2.5
  if (zoom <= 2) return 0.5
  if (zoom <= 3) return 0.8
  if (zoom <= 5) return 1.0
  return 1.5
}

export default function MapView({ geojson, resetKey = 0 }) {
  const [globalData, setGlobalData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [currentZoom, setCurrentZoom] = useState(DEFAULT_ZOOM)
  const [showOceanLabels, setShowOceanLabels] = useState(true)
  const { sendMessage, mode } = useChat()

  // Always fetch and retain the entire global fleet of floats
  useEffect(() => {
    setIsLoading(true)
    getMapData()
      .then((data) => {
        setGlobalData(data)
      })
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [])

  // Highlighted WMO IDs from chat query (if a specific float was asked)
  const highlightedWmoIds = useMemo(() => {
    if (!geojson?.features) return new Set()
    return new Set(
      geojson.features
        .map((f) => String(f.properties?.wmo_id))
        .filter((id) => id && id !== 'undefined')
    )
  }, [geojson])

  // Focus target coordinates for smooth camera fly-to
  const focusTarget = useMemo(() => {
    if (!geojson?.features || geojson.features.length === 0) return null
    // If specific subset (e.g. 1 to 5 floats), focus on the first one
    if (geojson.features.length <= 5) {
      const [lon, lat] = geojson.features[0].geometry.coordinates
      return { lat, lon }
    }
    return null
  }, [geojson])

  // Combine global fleet with any newly queried features
  const allFeatures = useMemo(() => {
    const base = globalData?.features || []
    if (!geojson?.features || geojson.features.length === 0) return base

    const existingWmos = new Set(base.map((f) => String(f.properties?.wmo_id)))
    const extras = geojson.features.filter((f) => !existingWmos.has(String(f.properties?.wmo_id)))
    return [...base, ...extras]
  }, [globalData, geojson])

  // Explorer handlers
  const handleAskAbout = useCallback((wmoId) => {
    sendMessage(`Tell me about float ${wmoId}`)
  }, [sendMessage])

  const handleAskLocation = useCallback((lat, lon) => {
    sendMessage(`What is the recent ocean data near latitude ${lat.toFixed(2)}, longitude ${lon.toFixed(2)}?`)
  }, [sendMessage])

  const handleAskOcean = useCallback((oceanName) => {
    sendMessage(`What is the average surface temperature and ocean conditions in the ${oceanName}?`)
  }, [sendMessage])

  const handleExploreOceanFloats = useCallback((oceanName) => {
    sendMessage(`Show all active floats and observations in the ${oceanName}`)
  }, [sendMessage])

  // Researcher handlers
  const handleInspectRawQC = useCallback((wmoId) => {
    sendMessage(`Show depth profile and QC flags for float ${wmoId}`)
  }, [sendMessage])

  const handleThermoclineLookup = useCallback((wmoId) => {
    sendMessage(`Calculate thermocline depth and MLD for float ${wmoId}`)
  }, [sendMessage])

  const handleCompareFloat = useCallback((wmoId) => {
    sendMessage(`Compare floats ${wmoId} and 2902183 across depth bins`)
  }, [sendMessage])

  // Cache ocean icon definitions
  const oceanIcons = useMemo(() => {
    const icons = {}
    MAJOR_OCEANS.forEach((ocean) => {
      icons[ocean.id] = L.divIcon({
        className: 'ocean-label-wrapper',
        html: `
          <div class="ocean-map-label ${ocean.type}" title="Explore ${ocean.name}">
            <span class="ocean-icon">${ocean.type === 'sea' ? '⚓' : '🌊'}</span>
            <span class="ocean-name-text">${ocean.name}</span>
          </div>
        `,
        iconSize: [160, 32],
        iconAnchor: [80, 16],
      })
    })
    return icons
  }, [])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Loading overlay */}
      {isLoading && (
        <div className="map-loading-overlay">
          <Loader2 size={28} className="spin" />
          <span>Loading global float fleet…</span>
        </div>
      )}

      <MapContainer
        center={CENTER}
        zoom={DEFAULT_ZOOM}
        minZoom={2}
        maxZoom={18}
        maxBounds={LAT_BOUNDS}
        maxBoundsViscosity={1.0}
        worldCopyJump={true}
        scrollWheelZoom={true}
        zoomControl={true}
        style={{ width: '100%', height: '100%' }}
      >
        <MapEventsController
          resetKey={resetKey}
          onZoomChange={setCurrentZoom}
          focusTarget={focusTarget}
        />
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
          noWrap={false}
        />

        {/* ── 7 Oceans & Regional Sea Labels (360° Infinite Wrapping) ───────── */}
        {showOceanLabels &&
          MAJOR_OCEANS.map((ocean) => (
            <React.Fragment key={ocean.id}>
              {WRAP_OFFSETS.map((offset) => (
                <Marker
                  key={`${ocean.id}-${offset}`}
                  position={[ocean.lat, ocean.lon + offset]}
                  icon={oceanIcons[ocean.id]}
                  zIndexOffset={100}
                >
                  <Popup>
                    <div className="float-popup ocean-popup">
                      <div className="ocean-popup-header">
                        <Globe size={15} style={{ display: 'inline', marginRight: 5, verticalAlign: 'middle' }} />
                        <strong>{ocean.name}</strong>
                      </div>
                      <p className="ocean-popup-desc">{ocean.desc}</p>
                      <div className="popup-actions">
                        <button
                          className="popup-action-btn"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleAskOcean(ocean.name)
                          }}
                        >
                          <MessageSquare size={12} />
                          Ask conditions & temperature
                        </button>
                        <button
                          className="popup-action-btn"
                          style={{ background: '#4f46e5' }}
                          onClick={(e) => {
                            e.stopPropagation()
                            handleExploreOceanFloats(ocean.name)
                          }}
                        >
                          <Compass size={12} />
                          Find floats in this region
                        </button>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </React.Fragment>
          ))}

        {/* ── Scaled ARGO Float Markers (Entire Global Fleet Preserved) ── */}
        {allFeatures.map((f, i) => {
          const [lon, lat] = f.geometry.coordinates
          const p = f.properties
          const isBgc = p.is_bgc
          const isHighlighted = highlightedWmoIds.has(String(p.wmo_id))

          const radius = getFloatDotRadius(isBgc, isHighlighted, currentZoom)
          const weight = getFloatDotWeight(isHighlighted, currentZoom)
          const keyPrefix = p.wmo_id || String(i)

          // Color coding: Golden/Amber for queried float, Cyan for BGC, Indigo for Core
          const dotColor = isHighlighted ? '#f59e0b' : isBgc ? '#06b6d4' : '#6366f1'
          const fillColor = isHighlighted ? '#fbbf24' : isBgc ? '#06b6d4' : '#6366f1'
          const fillOpacity = isHighlighted ? 1.0 : isBgc ? 0.88 : 0.8

          return (
            <React.Fragment key={`${keyPrefix}-${i}`}>
              {WRAP_OFFSETS.map((offset) => (
                <CircleMarker
                  key={`${keyPrefix}-${offset}`}
                  center={[lat, lon + offset]}
                  radius={radius}
                  zIndexOffset={isHighlighted ? 500 : 10}
                  pathOptions={{
                    color: dotColor,
                    fillColor: fillColor,
                    fillOpacity: fillOpacity,
                    weight: weight,
                  }}
                >
                  <Popup>
                    <div className="float-popup">
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <strong>WMO: {p.wmo_id}</strong>
                        {isHighlighted && (
                          <span className="focused-float-tag">
                            <Star size={10} fill="#f59e0b" color="#f59e0b" style={{ marginRight: 2 }} />
                            Queried Float
                          </span>
                        )}
                      </div>
                      {p.platform_type && <span>Type: {p.platform_type}<br /></span>}
                      {p.dac && <span>DAC: {p.dac}<br /></span>}
                      {isBgc && <span className="bgc-badge">BGC</span>}

                      {/* Mode-tailored actions */}
                      {mode === 'researcher' ? (
                        /* Researcher mode: Scientific raw data inspection */
                        <div className="popup-actions">
                          <button
                            className="popup-action-btn"
                            style={{ background: '#0284c7' }}
                            onClick={(e) => { e.stopPropagation(); handleInspectRawQC(p.wmo_id) }}
                          >
                            <Database size={12} />
                            Raw Profiles & QC Flags
                          </button>
                          <button
                            className="popup-action-btn"
                            style={{ background: '#0d9488' }}
                            onClick={(e) => { e.stopPropagation(); handleThermoclineLookup(p.wmo_id) }}
                          >
                            <Activity size={12} />
                            Thermocline & MLD
                          </button>
                          <button
                            className="popup-action-btn"
                            style={{ background: '#4f46e5' }}
                            onClick={(e) => { e.stopPropagation(); handleCompareFloat(p.wmo_id) }}
                          >
                            <GitCompare size={12} />
                            Compare Float
                          </button>
                        </div>
                      ) : (
                        /* Explorer mode: Friendly questions */
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
                      )}
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </React.Fragment>
          )
        })}
      </MapContainer>

      {/* Legend & Toggle */}
      <div className="map-legend">
        <div className="legend-title">Float Types & Basins</div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: '#6366f1' }}></span>
          <span>Standard Argo ({allFeatures.length} floats)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot legend-dot-lg" style={{ background: '#06b6d4' }}></span>
          <span>BGC-Argo</span>
        </div>
        {highlightedWmoIds.size > 0 && (
          <div className="legend-item" style={{ color: '#fbbf24', fontWeight: 600 }}>
            <span className="legend-dot" style={{ background: '#f59e0b', border: '1px solid #fbbf24' }}></span>
            <span>Queried Float ({highlightedWmoIds.size})</span>
          </div>
        )}
        <div className="legend-item" style={{ marginTop: '0.4rem', borderTop: '1px solid var(--border)', paddingTop: '0.4rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            <input
              type="checkbox"
              checked={showOceanLabels}
              onChange={(e) => setShowOceanLabels(e.target.checked)}
              style={{ accentColor: 'var(--accent)', cursor: 'pointer' }}
            />
            <span>Show Ocean Names</span>
          </label>
        </div>
      </div>
    </div>
  )
}
