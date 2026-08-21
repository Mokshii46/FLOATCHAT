# FloatChat — Demo Script (SIH 2025)

Rehearse these questions in order. All use cached/pre-warmed queries.
Run `scripts/seed_demo_data.py` before the demo to ensure data is loaded.

---

## Setup Checklist (30 mins before demo)

- [ ] `docker-compose up -d` — start all services
- [ ] Verify `http://localhost:5173` loads the UI
- [ ] Verify `http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] Run `python scripts/seed_demo_data.py` if live GDAC is unavailable
- [ ] Ensure LLM_API_KEY is set in `.env`
- [ ] Switch to **Citizen mode** for the opening questions

---

## Demo Sequence (~12 minutes)

### Opening (2 min) — Citizen Mode, English
**Q1**: "What is the average temperature in the Arabian Sea this year?"
- Expected: time-series chart + conversational summary
- Hits: template `avg_sst_region`, USP 6 (citizen mode)

**Q2**: "Is there anything unusual about the temperature trend?"
- Expected: anomaly banner showing z-score + narrative
- Hits: USP 1 (anomaly detection)

---

### BGC & Map (3 min)
**Q3**: "Show me all active BGC floats on the map."
- Expected: GeoJSON map with float markers
- Hits: template `list_bgc_floats`, map viz

**Q4**: "Show the chlorophyll profile for float 6904160."
- Expected: depth-profile chart, chlorophyll vs pressure
- Hits: template `chlorophyll_profile`, USP 7 (BGC)

---

### Trajectory & Prediction (2 min)
**Q5**: "Where is float 2902183 and where will it surface next?"
- Expected: trajectory map + prediction marker (USP 3)
- Hits: template `float_summary`, trajectory predictor

---

### Researcher Mode & Explainability (2 min)
- Toggle to **Researcher Mode**

**Q6**: "Compare temperature profiles of floats 2902183 and 2902200."
- Expected: overlaid depth-profile chart + raw data table + SQL panel
- Hits: template `compare_floats`, USP 5 (explainability), USP 6 (researcher mode)

---

### Multilingual & Voice (2 min) — USP 2 & USP 4
**Q7** (Hindi): "अरब सागर में लवणता कितनी है?"
  *(Translation: "What is the salinity in the Arabian Sea?")*
- Expected: same salinity result as English, answer in Hindi
- Hits: USP 2 (language detect + translate), template `salinity_region`

- Click the 🎤 mic button and **say** the same question in English
- Expected: transcription appears in chat box, answer returned
- Hits: USP 4 (voice input)

---

### Export (1 min)
**Q8**: "Can I download this data?"
- Click **Export CSV** button
- Hits: `/export/csv` endpoint

---

## Fallback Options (if live GDAC is slow)

If `fetch_by_region` times out:
1. Use seeded demo data: `python scripts/seed_demo_data.py --floats 5 --cycles 30`
2. Questions Q1–Q8 all work against seeded data.
3. Float WMO ids available: `2902183`, `2902200`, `6904160`, `6904161`, `2903740`

---

## Judge Talking Points

| USP | One-liner |
|-----|-----------|
| Anomaly detection | "Proactively flags statistically significant events in any region" |
| Multilingual | "Works in 7 Indian languages — no English required" |
| Trajectory prediction | "Predicts next surfacing with ML drift model" |
| Voice input | "Whisper STT — ask by speaking" |
| Explainability | "Every answer shows its SQL — scientists can verify" |
| Mode toggle | "Citizen-friendly summaries or researcher-grade raw data" |
| BGC-Argo | "Full support for oxygen, chlorophyll, pH, nitrate parameters" |
