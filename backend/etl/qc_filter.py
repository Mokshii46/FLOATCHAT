"""
QC filter — keeps only Argo "good" (1) and "probably good" (2) observations.

Argo QC flag definitions
  0 = no QC performed
  1 = good data            ← keep
  2 = probably good data   ← keep
  3 = probably bad data    ← drop
  4 = bad data             ← drop
  5 = value changed        ← keep (post-correction)
  6 = not used
  7 = not used
  8 = interpolated value   ← keep
  9 = missing value        ← drop
"""

from utils.logger import get_logger

logger = get_logger(__name__)

KEEP_FLAGS: frozenset[str] = frozenset({"1", "2", "5", "8"})


def _qc_ok(flag: str | None) -> bool:
    if flag is None:
        return True          # no QC info → include by default
    return str(flag).strip() in KEEP_FLAGS


def filter_profiles(rows: list[dict]) -> list[dict]:
    """
    Return only profile rows where ALL QC flags (pressure, temp, salinity)
    are in the keep set.  Rows missing a parameter but with good pressure
    are still included — e.g. missing salinity doesn't discard a valid T row.
    """
    before = len(rows)
    kept = []
    for r in rows:
        pres_ok = _qc_ok(r.get("pressure_qc"))
        temp_ok = _qc_ok(r.get("temperature_qc"))
        psal_ok = _qc_ok(r.get("salinity_qc"))

        # require at least pressure QC to be good
        if pres_ok and (temp_ok or psal_ok):
            kept.append(r)

    logger.info("QC filter: %d → %d profile rows (%.1f%% retained)",
                before, len(kept), 100 * len(kept) / before if before else 0)
    return kept


def filter_bgc_profiles(rows: list[dict]) -> list[dict]:
    """
    Keep BGC rows where at least one parameter has a valid QC flag.
    """
    bgc_qc_fields = [
        "dissolved_oxygen_qc", "chlorophyll_qc", "ph_qc", "nitrate_qc"
    ]
    before = len(rows)
    kept = [
        r for r in rows
        if any(_qc_ok(r.get(f)) for f in bgc_qc_fields)
    ]
    logger.info("BGC QC filter: %d → %d rows", before, len(kept))
    return kept