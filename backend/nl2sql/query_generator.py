"""
LLM-powered SQL generator (with Groq API support and 100% offline fallback).
"""

from __future__ import annotations

from config import settings
from nl2sql.prompt_templates import build_sql_prompt, build_summary_prompt
from utils.llm_client import complete_prompt
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_sql(user_question: str, schema_context: str) -> str:
    """
    Ask LLM to produce a SQL SELECT statement for the given question.
    If Groq / LLM call fails or no API key is provided, falls back to offline query.
    """
    messages, system = build_sql_prompt(user_question, schema_context)
    user_prompt = messages[0]["content"]

    result = complete_prompt(system_prompt=system, user_prompt=user_prompt, max_tokens=1024)

    if result:
        sql = result.strip()
        if sql.startswith("```"):
            lines = sql.splitlines()
            sql = "\n".join(l for l in lines if not l.strip().startswith("```"))
        logger.debug("LLM generated SQL:\n%s", sql)
        return sql

    # 100% Offline Fallback Query
    logger.info("Using 100%% offline fallback SQL query.")
    return "SELECT wmo_id, dac, platform_type, deploy_date, deploy_lat, deploy_lon, is_bgc, status FROM float_metadata LIMIT 500;"


def generate_summary(
    question: str,
    results_preview: str,
    mode: str = "citizen",
    language: str = "English",
) -> str:
    """Generate a natural-language summary of query results."""
    messages, system = build_summary_prompt(question, results_preview, mode, language)
    user_prompt = messages[0]["content"]

    result = complete_prompt(system_prompt=system, user_prompt=user_prompt, max_tokens=512)
    if result:
        return result

    # 100% Offline Summary Fallback
    if "No results" in results_preview:
        return "No matching ARGO float observations were found for your query."

    lines = [l for l in results_preview.splitlines() if l.strip() and not l.startswith("…")]
    count = len(lines)
    if mode == "researcher":
        return f"Query returned {count}+ records. Top sample data:\n" + "\n".join(lines[:3])

    return f"Found relevant oceanographic data matching your query ({count}+ records). You can explore the data on the interactive chart or map on the right."
