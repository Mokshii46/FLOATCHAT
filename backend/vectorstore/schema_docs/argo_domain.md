# Argo Float Domain Knowledge

This document provides domain context for the ARGO ocean float programme,
used to ground SQL generation and natural-language summaries.

---

## What is an Argo Float?

Argo is a global array of autonomous profiling floats that measure temperature
and salinity from the ocean surface down to 2000 m depth.  BGC-Argo floats
additionally measure oxygen, chlorophyll, nitrate, pH, and optical properties.

Each float:
- Drifts at a "parking depth" (~1000 dbar) for ~9 days
- Descends to 2000 dbar, then ascends while sampling
- Surfaces, transmits data via satellite, then re-submerges (one **cycle** ≈ 10 days)
- Is identified by a unique **WMO id** (a 7-digit number, e.g. 2902183)

---

## INCOIS and Indian Ocean Coverage

The Indian National Centre for Ocean Information Services (INCOIS) operates
the Indian Argo programme, maintaining floats across:

- **Arabian Sea** (lon 55–77°E, lat 5–25°N)
- **Bay of Bengal** (lon 80–98°E, lat 5–22°N)
- **Southern Indian Ocean** (lat 0–60°S)

The Data Assembly Centre (DAC) code for INCOIS floats is `"incois"`.

---

## QC Flag Definitions

Argo uses a numeric QC flag system:

| Flag | Meaning               | Include in analysis? |
|------|-----------------------|----------------------|
| 1    | Good data             | ✅ Yes |
| 2    | Probably good data    | ✅ Yes |
| 3    | Probably bad data     | ❌ No  |
| 4    | Bad data              | ❌ No  |
| 5    | Value changed (corrected) | ✅ Yes |
| 8    | Interpolated value    | ✅ Yes |
| 9    | Missing value         | ❌ No  |

The `floatchat` database only retains rows with flags 1, 2, 5, or 8.

---

## Physical Parameter Ranges (typical)

| Parameter      | Typical range   | Units   |
|----------------|-----------------|---------|
| Temperature    | –2 to 32        | °C      |
| Salinity       | 32 to 38        | PSU     |
| Pressure       | 0 to 2000       | dbar (≈ m) |
| Dissolved O₂   | 0 to 350        | µmol/kg |
| Chlorophyll-a  | 0 to 5          | mg/m³   |
| Nitrate        | 0 to 45         | µmol/kg |
| pH             | 7.8 to 8.4      | total scale |

---

## Oceanographic Concepts

- **Thermocline**: Layer of rapid temperature decrease with depth (~50–200 m in tropics)
- **Halocline**: Layer of rapid salinity change with depth
- **Mixed layer depth (MLD)**: Depth above which properties are near-uniform; typically 20–100 m
- **Potential density**: Density referenced to surface pressure; key for water mass identification
- **T-S diagram**: Plot of temperature vs salinity used to identify water masses
- **Indian Ocean Dipole (IOD)**: Climate mode affecting temperature/salinity anomalies in Indian Ocean

---

## Pressure vs Depth

Pressure in dbar is approximately equal to depth in meters for the ocean.
A pressure of 200 dbar ≈ 200 m depth; 1000 dbar ≈ 1000 m depth.

---

## Platform Types (common in Indian Ocean)

- **APEX** (Teledyne Webb): Most common float type; core Argo
- **NOVA** / **ARVOR**: CLS / NKE floats used by European programmes
- **SOLO** (SIO): Scripps Institution floats
- **NAVIS**: Sea-Bird BGC-capable float
