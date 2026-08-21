import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Chat ──────────────────────────────────────────────────────────

export const sendChat = (question, { mode, language, sessionId } = {}) =>
  api.post('/chat', { question, mode, language, session_id: sessionId }).then((r) => r.data)

// ── Floats ────────────────────────────────────────────────────────

export const listFloats = (params = {}) =>
  api.get('/floats', { params }).then((r) => r.data)

export const getFloat = (wmoId) =>
  api.get(`/floats/${wmoId}`).then((r) => r.data)

// ── Viz ───────────────────────────────────────────────────────────

export const getMapData = (params = {}) =>
  api.get('/viz/map', { params }).then((r) => r.data)

export const getDepthProfile = (wmoId, cycleNumber) =>
  api.get('/viz/profile', { params: { wmo_id: wmoId, cycle_number: cycleNumber } }).then((r) => r.data)

export const getTimeSeries = (params = {}) =>
  api.get('/viz/timeseries', { params }).then((r) => r.data)

// ── Voice ─────────────────────────────────────────────────────────

export const transcribeAudio = (audioBlob) => {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.webm')
  return api.post('/voice/transcribe', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

export const speakText = (text, lang = 'en') =>
  api.post('/voice/speak', { text, lang }).then((r) => r.data)

// ── Export ────────────────────────────────────────────────────────

export const getExportUrl = (sql) =>
  `${BASE_URL}/export/csv?sql=${encodeURIComponent(sql)}`

// ── Raw Query (debug) ─────────────────────────────────────────────

export const rawQuery = (sql) =>
  api.post('/query', { sql }).then((r) => r.data)

export default api
