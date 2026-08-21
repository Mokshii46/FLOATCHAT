# NL → SQL Query Examples

Few-shot examples for grounding the LLM's SQL generation.
Each example shows a natural-language question followed by the correct SQL.

---

## Example 1 — Temperature in a region

**Question**: What is the average sea surface temperature in the Arabian Sea in 2023?

```sql
SELECT AVG(p.temperature) AS avg_sst_celsius,
       MIN(p.temperature) AS min_temp,
       MAX(p.temperature) AS max_temp,
       COUNT(*) AS obs_count
FROM profiles p
WHERE p.lat BETWEEN 5 AND 25
  AND p.lon BETWEEN 55 AND 77
  AND p.pressure BETWEEN 0 AND 10
  AND p.timestamp BETWEEN '2023-01-01' AND '2023-12-31'
LIMIT 5000;
```

---

## Example 2 — Specific float trajectory

**Question**: Show me the path of float 2902183.

```sql
SELECT tp.cycle_number, tp.timestamp, tp.lat, tp.lon
FROM trajectory_points tp
JOIN float_metadata fm ON tp.float_id = fm.id
WHERE fm.wmo_id = '2902183'
ORDER BY tp.cycle_number ASC
LIMIT 5000;
```

---

## Example 3 — Depth profile

**Question**: Give me the temperature vs depth profile for float 2902183 on its 45th cycle.

```sql
SELECT p.pressure, p.temperature, p.salinity, p.temperature_qc, p.salinity_qc
FROM profiles p
JOIN float_metadata fm ON p.float_id = fm.id
WHERE fm.wmo_id = '2902183'
  AND p.cycle_number = 45
ORDER BY p.pressure ASC
LIMIT 5000;
```

---

## Example 4 — Monthly mean salinity trend

**Question**: How has salinity changed month by month in the Bay of Bengal over the past year?

```sql
SELECT DATE_TRUNC('month', p.timestamp) AS month,
       AVG(p.salinity) AS avg_salinity,
       COUNT(*) AS n_obs
FROM profiles p
WHERE p.lat BETWEEN 5 AND 22
  AND p.lon BETWEEN 80 AND 98
  AND p.timestamp >= NOW() - INTERVAL '1 year'
GROUP BY month
ORDER BY month ASC
LIMIT 5000;
```

---

## Example 5 — Comparing two floats

**Question**: Compare temperature profiles of floats 2902183 and 2902200.

```sql
SELECT fm.wmo_id, p.pressure, AVG(p.temperature) AS avg_temp
FROM profiles p
JOIN float_metadata fm ON p.float_id = fm.id
WHERE fm.wmo_id IN ('2902183', '2902200')
GROUP BY fm.wmo_id, p.pressure
ORDER BY fm.wmo_id, p.pressure
LIMIT 5000;
```

---

## Example 6 — BGC chlorophyll depth profile (USP 7)

**Question**: Show chlorophyll concentration vs depth for float 6904160.

```sql
SELECT b.pressure, b.chlorophyll, b.chlorophyll_qc
FROM bgc_profiles b
JOIN float_metadata fm ON b.float_id = fm.id
WHERE fm.wmo_id = '6904160'
  AND b.chlorophyll IS NOT NULL
ORDER BY b.pressure ASC
LIMIT 5000;
```

---

## Example 7 — Active BGC floats list

**Question**: List all active BGC floats.

```sql
SELECT wmo_id, dac, platform_type, deploy_date, deploy_lat, deploy_lon
FROM float_metadata
WHERE is_bgc = true AND status = 'active'
ORDER BY deploy_date DESC
LIMIT 5000;
```

---

## Example 8 — Dissolved oxygen trend

**Question**: How has dissolved oxygen changed at 200m depth in the Arabian Sea?

```sql
SELECT DATE_TRUNC('month', b.timestamp) AS month,
       AVG(b.dissolved_oxygen) AS avg_oxygen
FROM bgc_profiles b
WHERE b.lat BETWEEN 5 AND 25
  AND b.lon BETWEEN 55 AND 77
  AND b.pressure BETWEEN 190 AND 210
GROUP BY month
ORDER BY month ASC
LIMIT 5000;
```

---

## Key Rules

1. Always use `LIMIT 5000` (enforced by the validator even if omitted here).
2. Join through `float_metadata` to filter by `wmo_id` — never use `float_id` directly in the API.
3. Use `p.pressure BETWEEN 0 AND 10` for "sea surface" queries.
4. Use `DATE_TRUNC('month', timestamp)` for monthly aggregations.
5. Never use DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER, or any DDL.
