"""
Mode service — USP 6.

Manages citizen-science vs researcher mode logic.

Citizen mode:
  - Simplified NL summaries, no jargon
  - Guided prompt suggestions shown
  - SQL hidden by default in ExplainabilityPanel

Researcher mode:
  - Raw data table + QC flags visible
  - SQL exposed by default
  - Full numeric precision in summaries
"""

from __future__ import annotations

from config import settings

VALID_MODES = {"citizen", "researcher"}


def get_mode_config(mode: str | None = None) -> dict:
    """
    Return mode-specific configuration flags used by chat_service
    and the frontend.
    """
    effective_mode = (mode or settings.default_mode).lower()
    if effective_mode not in VALID_MODES:
        effective_mode = "citizen"

    if effective_mode == "researcher":
        return {
            "mode": "researcher",
            "show_sql": True,
            "show_qc_flags": True,
            "summary_style": "technical",
            "numeric_precision": 4,
            "guided_prompts": False,
            "default_viz": "table",
        }
    else:
        return {
            "mode": "citizen",
            "show_sql": False,
            "show_qc_flags": False,
            "summary_style": "plain",
            "numeric_precision": 2,
            "guided_prompts": True,
            "default_viz": "auto",
        }


def get_summary_instruction(mode: str) -> str:
    """Return a sentence injected into the LLM summary prompt for the given mode."""
    if mode == "researcher":
        return (
            "Use precise scientific language. Include exact values, units, "
            "and note any QC or data-coverage caveats."
        )
    return (
        "Use plain, friendly language. Avoid jargon. "
        "Highlight the single most interesting finding in one sentence."
    )
