"""
Apply Argo QC-flag filtering per the Argo QC manual:
  1 = good, 2 = probably good, 3 = probably bad, 4 = bad,
  5 = changed, 8 = estimated, 9 = missing.

We keep 1 and 2 by default ("good" / "probably good"). Rows failing QC
on a given variable have that variable nulled rather than the whole row
dropped, unless `drop_failed_rows=True` — pressure failing QC always
drops the row since depth is required.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

GOOD_FLAGS = {"1", "2"}


def qc_filter(
    df: pd.DataFrame,
    qc_column_pairs: list[tuple[str, str]],
    drop_failed_rows: bool = False,
) -> pd.DataFrame:
    """
    qc_column_pairs: list of (value_col, qc_col) tuples, e.g.
        [("temperature", "temperature_qc"), ("salinity", "salinity_qc")]
    """
    df = df.copy()
    before = len(df)

    for value_col, qc_col in qc_column_pairs:
        if qc_col not in df.columns or value_col not in df.columns:
            continue
        is_bad = ~df[qc_col].astype(str).str.strip().isin(GOOD_FLAGS)
        if drop_failed_rows:
            df = df[~is_bad]
        else:
            df.loc[is_bad, value_col] = None

    # Pressure (depth) is load-bearing — always drop rows without it
    if "pressure" in df.columns:
        df = df.dropna(subset=["pressure"])
    if "pressure_qc" in df.columns:
        bad_pressure = ~df["pressure_qc"].astype(str).str.strip().isin(GOOD_FLAGS)
        df = df[~bad_pressure]

    logger.info("QC filter: %d -> %d rows (dropped %d)", before, len(df), before - len(df))
    return df


def qc_filter_core(df: pd.DataFrame) -> pd.DataFrame:
    return qc_filter(
        df,
        qc_column_pairs=[
            ("temperature", "temperature_qc"),
            ("salinity", "salinity_qc"),
        ],
    )


def qc_filter_bgc(df: pd.DataFrame) -> pd.DataFrame:
    return qc_filter(
        df,
        qc_column_pairs=[
            ("dissolved_oxygen", "dissolved_oxygen_qc"),
            ("chlorophyll", "chlorophyll_qc"),
            ("ph", "ph_qc"),
            ("nitrate", "nitrate_qc"),
        ],
    )