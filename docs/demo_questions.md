# FloatChat — Demo Questions for Judges

A curated list of questions that exercise all response types, features, and modes.
Judges can read these out verbatim during the demo.

---

## Explorer Mode (start here)

### 1. Time-Series Query → Chart
**"What is the average temperature in the Arabian Sea this year?"**
- Expected: Monthly time-series chart + friendly summary
- Tests: Template routing, viz shaping, Explorer-mode summary

### 2. Single-Point Query → Stat Card
**"What is the current temperature at float 2902183?"**
- Expected: Visually appealing stat card with large number + unit
- Tests: Single-value response rendering (StatCard component)

### 3. Map Query → GeoJSON Map
**"Show me all active BGC floats on the map."**
- Expected: Interactive map with cyan BGC float markers
- Tests: Map viz, BGC filter, legend visibility

### 4. Depth Profile → Chart
**"Chlorophyll profile for float 6904160."**
- Expected: Depth-profile chart (chlorophyll vs pressure, depth increasing downward)
- Tests: BGC template, depth-profile rendering

### 5. Trajectory Prediction
**"Where will float 2902183 surface next?"**
- Expected: Map with dashed prediction line + confidence marker
- Tests: Trajectory prediction ML model, float summary template

### 6. Anomaly Detection
**"Is there anything unusual about temperatures in the Bay of Bengal recently?"**
- Expected: Anomaly banner (if anomaly detected) OR normal result with explanation
- Tests: Region-aware anomaly detection, z-score computation, banner rendering

### 7. Multilingual (Hindi)
**"अरब सागर में लवणता कितनी है?"**
*(Translation: "What is the salinity in the Arabian Sea?")*
- Expected: Salinity chart + answer in Hindi
- Tests: Language detection, translation pipeline, salinity template

---

## Researcher Mode (toggle mode, then ask)

### 8. Researcher-Mode Query (same question as #1)
**"What is the average temperature in the Arabian Sea this year?"**
- Expected: Same data BUT with SQL query visible inline, QC context in summary,
  full numeric precision, raw data table available
- Tests: Mode differentiation — visibly different result shape from Explorer

### 9. Explainability
**"Compare temperature profiles of floats 2902183 and 2902200."**
- Expected: Overlaid depth-profile chart + visible SQL panel + template info
- Tests: Compare template, explainability panel, researcher-mode styling

---

## Float-Click Demo (from map)

### 10. Click any float on the map
- Click the indigo or cyan dot → popup appears
- Click **"Ask about this float"** → chat auto-sends question about that WMO ID
- Click **"Ask about this location"** → chat asks about nearby ocean data
- Tests: Map-to-chat interaction, float_about template

---

## Edge Cases & Features

### 11. Voice Input
- Click the 🎤 mic button and **say**: "Show me active floats in the Arabian Sea"
- Tests: Whisper STT, voice pipeline

### 12. Chat Edit
- After getting an answer, click the ✏️ edit button on your question
- Modify it and submit → old message + answer replaced with new conversation
- Tests: Edit-and-regenerate flow

### 13. Chat History
- Clear the chat, start a new conversation
- Open the history dropdown → see past conversations
- Click a past session to reload it
- Tests: localStorage persistence, session management

### 14. Export
- After any data query, click **"Export CSV"** below the chat input
- Tests: CSV export endpoint

---

## Response Type Summary

| Question Type       | Expected Rendering     | Example Question |
|--------------------|-----------------------|------------------|
| Time series        | Line chart (Plotly)   | #1, #8           |
| Single value       | StatCard              | #2               |
| Map/location       | Leaflet GeoJSON       | #3               |
| Depth profile      | Scatter chart (Plotly) | #4, #9           |
| Trajectory         | Map + prediction line | #5               |
| Anomaly            | Warning/critical banner | #6             |
| Multilingual       | Same viz + translated text | #7           |
