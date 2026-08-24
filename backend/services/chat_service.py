"""
Chat service — orchestrates the full FloatChat pipeline.

Pipeline
--------
1. Detect language (USP 2)
2. Translate to English if needed (USP 2)
3. Route question → SQL (template or LLM) via nl2sql.router
4. Execute SQL → rows
5. Shape rows for visualisation via viz_service
6. Generate NL summary via LLM (USP 6 mode-aware)
7. Translate summary back to user language (USP 2)
8. Attach anomaly banner if relevant (USP 1)
9. Build explainability payload (USP 5)
10. Return structured ChatResponse dict
"""

from __future__ import annotations

from typing import Any

from nl2sql.router import route
from services.query_service import execute_query, preview_rows
from services.viz_service import shape_results
from services.mode_service import get_mode_config, get_summary_instruction
from services.explainability_service import build_payload
from services.translation_service import detect_language, translate_to_english, translate_from_english
from nl2sql.query_generator import generate_summary
from utils.logger import get_logger

logger = get_logger(__name__)


def process_chat(
    question: str,
    mode: str | None = None,
    language: str | None = None,
    session_context: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Full chat pipeline.

    Parameters
    ----------
    question        : raw user question (may be in any supported language)
    mode            : "citizen" | "researcher" (overrides settings default)
    language        : ISO 639-1 code override (detected automatically if None)
    session_context : previous Q&A pairs for follow-up resolution (future use)

    Returns
    -------
    dict with keys: answer, viz, anomaly, explainability, mode_config, language, row_count
    """
    mode_config = get_mode_config(mode)

    # 1–2. Language detection + translation
    detected_lang = language or detect_language(question)
    english_question = translate_to_english(question, detected_lang)
    logger.info("Question [%s->en]: %s", detected_lang, english_question[:80])

    # 3. Route → SQL
    try:
        route_result = route(english_question)
        sql = route_result["sql"]
    except Exception as exc:
        logger.error("NL2SQL routing failed: %s", exc)
        return _error_response(
            "I couldn't understand your query well enough to search the database. "
            "Try rephrasing, e.g.: 'Show active floats' or 'Temperature in Arabian Sea'.",
            mode_config, detected_lang
        )

    rag_context = ""
    if route_result["source"] == "llm":
        try:
            from vectorstore.chroma_client import get_chroma_client
            rag_context = get_chroma_client().get_relevant_context(english_question)
        except Exception as exc:
            logger.debug("RAG context retrieval failed: %s", exc)

    # 4. Execute
    try:
        rows = execute_query(sql)
    except Exception as exc:
        logger.error("Query execution failed: %s", exc)
        return _error_response(
            f"The database query failed: {exc}. "
            "This might be a temporary issue — try a simpler question.",
            mode_config, detected_lang
        )

    # 5. Shape viz
    if rows:
        viz_payload = shape_results(rows)
    else:
        viz_payload = {"viz_type": "table", "data": {"rows": []}, "row_count": 0}

    # 6. Generate summary
    if rows:
        preview = preview_rows(rows)
        mode_instruction = get_summary_instruction(mode_config["mode"])

        summary_en = generate_summary(
            question=english_question,
            results_preview=f"{preview}\n\nStyle instruction: {mode_instruction}",
            mode=mode_config["mode"],
            language="English",
        )
    else:
        summary_en = (
            "I searched the ARGO float database but didn't find any data matching your query. "
            "This could mean the specific float ID, region, or time range has no observations. "
            "Try asking about 'active floats', 'temperature in Arabian Sea', or 'BGC floats'."
        )

    # 7. Translate summary back
    answer = translate_from_english(summary_en, detected_lang)

    # 8. Anomaly check (lightweight: only on timeseries results)
    anomaly_payload: dict | None = None
    if rows and viz_payload["viz_type"] in ("timeseries", "table") and len(rows) > 3:
        try:
            from services.anomaly_service import detect_anomaly
            from nl2sql.router import _detect_region

            # Extract the actual region and parameter from the user's query
            bbox = _detect_region(english_question)
            region_map = {
                (5.0, 25.0, 55.0, 77.0): "arabian_sea",
                (5.0, 22.0, 80.0, 98.0): "bay_of_bengal",
                (-60.0, 30.0, 20.0, 120.0): "indian_ocean",
                (0.0, 30.0, 45.0, 100.0): "north_indian_ocean",
                (-60.0, 0.0, 20.0, 120.0): "south_indian_ocean",
                (8.0, 14.0, 71.0, 75.0): "lakshadweep",
                (7.0, 15.0, 92.0, 99.0): "andaman_sea",
                (23.0, 30.0, 48.0, 57.0): "persian_gulf",
            }
            detected_region = region_map.get(bbox, "indian_ocean") if bbox else "indian_ocean"

            # Detect which parameter the user asked about
            q_lower = english_question.lower()
            if any(w in q_lower for w in ("salinity", "sal")):
                detected_param = "salinity"
            elif any(w in q_lower for w in ("oxygen", "o2", "dissolved")):
                detected_param = "dissolved_oxygen"
            else:
                detected_param = "temperature"

            anomaly = detect_anomaly(region=detected_region, parameter=detected_param)
            if anomaly.severity != "normal":
                anomaly_payload = {
                    "severity": anomaly.severity,
                    "narrative": translate_from_english(anomaly.narrative, detected_lang),
                    "z_score": anomaly.z_score,
                    "parameter": anomaly.parameter,
                    "region": anomaly.region,
                }
        except Exception as exc:
            logger.debug("Anomaly check skipped: %s", exc)

    # 9. Explainability
    explain = build_payload(route_result, rag_context)

    return {
        "answer": answer,
        "viz": viz_payload,
        "anomaly": anomaly_payload,
        "explainability": explain,
        "mode_config": mode_config,
        "language": detected_lang,
        "row_count": len(rows),
    }


def _lang_name(code: str) -> str:
    from services.translation_service import SUPPORTED_LANGUAGES
    return SUPPORTED_LANGUAGES.get(code, "English")


def _error_response(message: str, mode_config: dict, lang: str = "en") -> dict:
    return {
        "answer": message,
        "viz": None,
        "anomaly": None,
        "explainability": None,
        "mode_config": mode_config,
        "language": lang,
        "row_count": 0,
    }
