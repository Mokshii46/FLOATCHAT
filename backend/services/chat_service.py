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
    dict with keys: answer, viz, anomaly, explainability, mode_config, language
    """
    mode_config = get_mode_config(mode)

    # 1–2. Language detection + translation
    detected_lang = language or detect_language(question)
    english_question = translate_to_english(question, detected_lang)
    logger.info("Question [%s→en]: %s", detected_lang, english_question[:80])

    # 3. Route → SQL
    route_result = route(english_question)
    sql = route_result["sql"]
    rag_context = ""

    if route_result["source"] == "llm":
        from vectorstore.chroma_client import get_chroma_client
        rag_context = get_chroma_client().get_relevant_context(english_question)

    # 4. Execute
    try:
        rows = execute_query(sql)
    except Exception as exc:
        logger.error("Query execution failed: %s", exc)
        return _error_response(str(exc), mode_config)

    # 5. Shape viz
    viz_payload = shape_results(rows)

    # 6. Generate summary
    preview = preview_rows(rows)
    mode_instruction = get_summary_instruction(mode_config["mode"])
    lang_name = _lang_name(detected_lang)

    summary_en = generate_summary(
        question=english_question,
        results_preview=f"{preview}\n\nStyle instruction: {mode_instruction}",
        mode=mode_config["mode"],
        language="English",
    )

    # 7. Translate summary back
    answer = translate_from_english(summary_en, detected_lang)

    # 8. Anomaly check (lightweight: only on timeseries results)
    anomaly_payload: dict | None = None
    if viz_payload["viz_type"] in ("timeseries", "table") and len(rows) > 3:
        try:
            from services.anomaly_service import detect_anomaly
            anomaly = detect_anomaly()
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


def _error_response(message: str, mode_config: dict) -> dict:
    return {
        "answer": f"Sorry, I encountered an error running your query: {message}",
        "viz": None,
        "anomaly": None,
        "explainability": None,
        "mode_config": mode_config,
        "language": "en",
        "row_count": 0,
    }
