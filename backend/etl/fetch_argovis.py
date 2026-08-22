"""
Argovis REST API fetcher — downloads real Argo float data via the
Argovis v2 API (https://argovis-api.colorado.edu).

Returns row dicts in the same format that load_to_db.py expects,
so the rest of the pipeline (QC → load → ML) stays unchanged.

API structure notes (Argovis v2):
    - /argo          : profile data — accepts polygon, platform, data params
    - /argo/meta     : float metadata — accepts platform (NOT polygon)
    - data field is COLUMN-oriented: data[0]=pressure, data[1]=temp, etc.
    - data_info[0] = list of variable names matching data columns
    - compression=minimal returns compact [id, lon, lat, ts, sources, meta] arrays

Usage:
    from etl.fetch_argovis import fetch_indian_ocean_data
    result = fetch_indian_ocean_data()
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

import requests

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://argovis-api.colorado.edu"

# Indian Ocean bounding polygon [lon, lat] pairs (closed ring)
INDIAN_OCEAN_POLYGON = "[[20,-60],[20,30],[120,30],[120,-60],[20,-60]]"

# Rate limit: serial requests with a pause between each
REQUEST_DELAY_SECONDS = 1.2
MAX_RETRIES = 3
RETRY_BACKOFF = 5.0


# ── HTTP helpers ──────────────────────────────────────────────────

def _headers() -> dict:
    """Build request headers with optional API key."""
    h = {"Accept": "application/json"}
    if settings.argovis_api_key:
        h["x-argokey"] = settings.argovis_api_key
    return h


def _get(url: str, params: dict | None = None) -> list | dict | None:
    """GET with retry/backoff. Returns parsed JSON or None on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, headers=_headers(), timeout=60)
            if resp.status_code == 429:
                wait = RETRY_BACKOFF * (attempt + 1)
                logger.warning("Rate limited (429). Waiting %.0fs …", wait)
                time.sleep(wait)
                continue
            if resp.status_code == 404:
                return []  # no data for this query
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as exc:
            logger.warning("Request failed (attempt %d/%d): %s", attempt + 1, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF)
    logger.error("All retries exhausted for %s", url)
    return None


# ── Step 1: Discover floats in region ─────────────────────────────

def discover_platforms(
    polygon: str | None = None,
    days_back: int = 21,
) -> list[dict]:
    """
    Discover active floats in a region using a recent date window.
    Uses compression=minimal for fast discovery.

    Returns list of dicts: {"wmo_id": str, "is_bgc": bool}
    """
    polygon = polygon or INDIAN_OCEAN_POLYGON
    end = datetime.utcnow()
    start = end - timedelta(days=days_back)

    logger.info("Discovering floats in Indian Ocean (last %d days) …", days_back)

    data = _get(f"{BASE_URL}/argo", params={
        "polygon": polygon,
        "startDate": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endDate": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "compression": "minimal",
    })

    if not data or not isinstance(data, list):
        logger.warning("No platforms discovered.")
        return []

    # minimal format: [id, lon, lat, timestamp, sources_list, metadata_list]
    platforms: dict[str, dict] = {}
    for item in data:
        try:
            doc_id = item[0]
            wmo_id = doc_id.rsplit("_", 1)[0]
            sources = item[4] if len(item) > 4 else []
            is_bgc = "argo_bgc" in sources
            if wmo_id not in platforms:
                platforms[wmo_id] = {"wmo_id": wmo_id, "is_bgc": is_bgc}
            elif is_bgc:
                platforms[wmo_id]["is_bgc"] = True
        except (IndexError, TypeError):
            continue

    result = list(platforms.values())
    bgc_count = sum(1 for p in result if p["is_bgc"])
    logger.info("Discovered %d platforms (%d BGC).", len(result), bgc_count)
    return result


# ── Step 2: Fetch metadata for a float ────────────────────────────

def fetch_float_metadata(wmo_id: str) -> dict:
    """Fetch metadata for a single float from /argo/meta?platform=..."""
    time.sleep(REQUEST_DELAY_SECONDS * 0.5)  # lighter rate for meta
    data = _get(f"{BASE_URL}/argo/meta", params={"platform": wmo_id})

    meta = {
        "wmo_id": wmo_id,
        "dac": "",
        "platform_type": "",
        "project_name": "",
        "pi_name": "",
        "is_bgc": False,
        "status": "active",
    }

    if not data or not isinstance(data, list) or len(data) == 0:
        return meta

    doc = data[0]
    meta["dac"] = str(doc.get("data_center", "")).lower()
    meta["platform_type"] = str(doc.get("platform_type", ""))
    pi = doc.get("pi_name", "")
    meta["pi_name"] = pi[0] if isinstance(pi, list) and pi else str(pi)

    # Check for BGC in data_keys_mode
    dkm = doc.get("data_keys_mode", {})
    bgc_keys = {"doxy", "chla", "ph_in_situ_total", "nitrate", "bbp700"}
    if dkm and bgc_keys.intersection(set(k.lower() for k in dkm.keys())):
        meta["is_bgc"] = True

    return meta


# ── Step 3: Fetch core profiles for a float ──────────────────────

def fetch_profiles_for_platform(
    wmo_id: str,
    start_date: str,
    end_date: str,
) -> tuple[list[dict], list[dict]]:
    """
    Fetch all core profiles for a single float.
    Returns (profile_rows, trajectory_rows) in load_to_db format.

    Argovis data is COLUMN-oriented:
        data_info[0] = ["pressure", "temperature", "salinity"]
        data[0] = [all pressure values]
        data[1] = [all temperature values]
        data[2] = [all salinity values]
    """
    time.sleep(REQUEST_DELAY_SECONDS)
    data = _get(f"{BASE_URL}/argo", params={
        "platform": wmo_id,
        "startDate": start_date,
        "endDate": end_date,
        "data": "pressure,temperature,salinity",
    })

    if not data or not isinstance(data, list):
        return [], []

    profile_rows: list[dict] = []
    traj_seen: dict[int, dict] = {}

    for doc in data:
        cycle_number = doc.get("cycle_number", 0)

        # Geolocation (GeoJSON: [lon, lat])
        geolocation = doc.get("geolocation", {})
        coords = geolocation.get("coordinates", [None, None])
        lon = coords[0] if len(coords) >= 2 else None
        lat = coords[1] if len(coords) >= 2 else None

        # Timestamp
        ts = _parse_timestamp(doc.get("timestamp"))

        # Column-oriented data
        data_info = doc.get("data_info", [])
        levels_data = doc.get("data", [])

        if not levels_data or not data_info:
            continue

        col_names = data_info[0] if len(data_info) > 0 else []
        col_index = {name.lower(): i for i, name in enumerate(col_names)}

        pres_idx = col_index.get("pressure")
        temp_idx = col_index.get("temperature")
        sal_idx = col_index.get("salinity")

        if pres_idx is None or pres_idx >= len(levels_data):
            continue

        n_levels = len(levels_data[pres_idx])

        for i in range(n_levels):
            pressure = _safe_val(levels_data, pres_idx, i)
            if pressure is None:
                continue

            temperature = _safe_val(levels_data, temp_idx, i)
            salinity = _safe_val(levels_data, sal_idx, i)

            # Skip levels with no T or S data
            if temperature is None and salinity is None:
                continue

            profile_rows.append({
                "wmo_id": wmo_id,
                "cycle_number": cycle_number,
                "timestamp": ts,
                "lat": lat,
                "lon": lon,
                "pressure": pressure,
                "temperature": temperature,
                "salinity": salinity,
                "pressure_qc": "1",
                "temperature_qc": "1" if temperature is not None else None,
                "salinity_qc": "1" if salinity is not None else None,
            })

        # Trajectory: one entry per cycle
        if cycle_number not in traj_seen and lat is not None and lon is not None:
            traj_seen[cycle_number] = {
                "wmo_id": wmo_id,
                "cycle_number": cycle_number,
                "timestamp": ts,
                "lat": lat,
                "lon": lon,
            }

    trajectory_rows = list(traj_seen.values())
    return profile_rows, trajectory_rows


# ── Step 4: Fetch BGC profiles for a float ────────────────────────

def fetch_bgc_for_platform(
    wmo_id: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """Fetch BGC profiles for a single BGC-capable float."""
    time.sleep(REQUEST_DELAY_SECONDS)
    data = _get(f"{BASE_URL}/argo", params={
        "platform": wmo_id,
        "startDate": start_date,
        "endDate": end_date,
        "data": "pressure,doxy,chla,ph_in_situ_total,nitrate,bbp700",
    })

    if not data or not isinstance(data, list):
        return []

    bgc_rows: list[dict] = []

    for doc in data:
        cycle_number = doc.get("cycle_number", 0)
        geolocation = doc.get("geolocation", {})
        coords = geolocation.get("coordinates", [None, None])
        lon = coords[0] if len(coords) >= 2 else None
        lat = coords[1] if len(coords) >= 2 else None
        ts = _parse_timestamp(doc.get("timestamp"))

        data_info = doc.get("data_info", [])
        levels_data = doc.get("data", [])

        if not levels_data or not data_info:
            continue

        col_names = data_info[0] if len(data_info) > 0 else []
        col_index = {name.lower(): i for i, name in enumerate(col_names)}

        pres_idx = col_index.get("pressure")
        doxy_idx = col_index.get("doxy")
        chla_idx = col_index.get("chla")
        ph_idx = col_index.get("ph_in_situ_total")
        nitrate_idx = col_index.get("nitrate")
        bbp_idx = col_index.get("bbp700")

        if pres_idx is None or pres_idx >= len(levels_data):
            continue

        n_levels = len(levels_data[pres_idx])

        for i in range(n_levels):
            pressure = _safe_val(levels_data, pres_idx, i)
            if pressure is None:
                continue

            doxy = _safe_val(levels_data, doxy_idx, i)
            chla = _safe_val(levels_data, chla_idx, i)
            ph = _safe_val(levels_data, ph_idx, i)
            nitrate = _safe_val(levels_data, nitrate_idx, i)
            bbp = _safe_val(levels_data, bbp_idx, i)

            if all(v is None for v in (doxy, chla, ph, nitrate, bbp)):
                continue

            bgc_rows.append({
                "wmo_id": wmo_id,
                "cycle_number": cycle_number,
                "timestamp": ts,
                "lat": lat,
                "lon": lon,
                "pressure": pressure,
                "dissolved_oxygen": doxy,
                "chlorophyll": chla,
                "ph": ph,
                "nitrate": nitrate,
                "backscatter": bbp,
                "dissolved_oxygen_qc": "1" if doxy is not None else None,
                "chlorophyll_qc": "1" if chla is not None else None,
                "ph_qc": "1" if ph is not None else None,
                "nitrate_qc": "1" if nitrate is not None else None,
            })

    return bgc_rows


# ── Helpers ───────────────────────────────────────────────────────

def _parse_timestamp(ts_str: str | None) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None


def _safe_val(levels_data: list, col_idx: int | None, row_idx: int) -> float | None:
    """Safely extract a value from column-oriented data."""
    if col_idx is None or col_idx >= len(levels_data):
        return None
    col = levels_data[col_idx]
    if row_idx >= len(col):
        return None
    v = col[row_idx]
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ── High-level orchestrator ──────────────────────────────────────

def fetch_indian_ocean_data(
    max_floats: int = 80,
    years_back: int | None = None,
) -> dict[str, list[dict]]:
    """
    Fetch real Argo data for the Indian Ocean.

    Returns a dict with keys:
        "float_metadata", "profiles", "trajectories", "bgc_profiles"
    """
    years = years_back or settings.argo_lookback_years
    end_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    start_date = (datetime.utcnow() - timedelta(days=365 * years)).strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info("=" * 60)
    logger.info("ARGOVIS FETCH: Indian Ocean, last %d years", years)
    logger.info("=" * 60)

    # Step 1: Discover platforms in the region
    discovered = discover_platforms()
    if not discovered:
        logger.error("No platforms discovered. Check API key and connectivity.")
        return {"float_metadata": [], "profiles": [], "trajectories": [], "bgc_profiles": []}

    # Limit floats and prioritise BGC floats (more interesting for demos)
    bgc_floats = [f for f in discovered if f["is_bgc"]]
    core_floats = [f for f in discovered if not f["is_bgc"]]
    # Take all BGC (up to half the limit) + fill rest with core
    n_bgc = min(len(bgc_floats), max_floats // 2)
    n_core = min(len(core_floats), max_floats - n_bgc)
    selected = bgc_floats[:n_bgc] + core_floats[:n_core]

    logger.info("Selected %d floats (%d BGC + %d core) out of %d discovered.",
                 len(selected), n_bgc, n_core, len(discovered))

    all_metas: list[dict] = []
    all_profiles: list[dict] = []
    all_trajectories: list[dict] = []
    all_bgc: list[dict] = []

    # Step 2: Fetch each float
    for i, platform in enumerate(selected):
        wmo_id = platform["wmo_id"]
        is_bgc = platform["is_bgc"]

        logger.info("[%d/%d] Fetching float %s (BGC=%s) …",
                     i + 1, len(selected), wmo_id, is_bgc)

        # Fetch metadata
        meta = fetch_float_metadata(wmo_id)
        meta["is_bgc"] = meta["is_bgc"] or is_bgc  # merge BGC detection

        # Fetch core profiles
        profiles, trajectories = fetch_profiles_for_platform(wmo_id, start_date, end_date)
        all_profiles.extend(profiles)
        all_trajectories.extend(trajectories)

        # Update deploy info from earliest trajectory point
        if trajectories:
            first = min(trajectories, key=lambda t: t.get("cycle_number", 0))
            meta["deploy_lat"] = first.get("lat")
            meta["deploy_lon"] = first.get("lon")
            if first.get("timestamp"):
                ts = first["timestamp"]
                meta["deploy_date"] = ts.date() if isinstance(ts, datetime) else ts

        # Fetch BGC if applicable
        if is_bgc:
            bgc = fetch_bgc_for_platform(wmo_id, start_date, end_date)
            all_bgc.extend(bgc)
            logger.info("  -> %d profiles, %d trajectories, %d BGC levels",
                         len(profiles), len(trajectories), len(bgc))
        else:
            logger.info("  -> %d profiles, %d trajectories",
                         len(profiles), len(trajectories))

        all_metas.append(meta)

    logger.info("=" * 60)
    logger.info("FETCH COMPLETE: %d floats, %d profiles, %d trajectories, %d BGC",
                 len(all_metas), len(all_profiles), len(all_trajectories), len(all_bgc))
    logger.info("=" * 60)

    return {
        "float_metadata": all_metas,
        "profiles": all_profiles,
        "trajectories": all_trajectories,
        "bgc_profiles": all_bgc,
    }
