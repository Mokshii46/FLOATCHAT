"""
Prompt templates for NL → SQL via Claude.

The system prompt is constructed once and cached; it injects:
  - The database schema (from RAG context)
  - Few-shot examples (from RAG context)
  - Hard rules about SQL safety
"""

SYSTEM_PROMPT_BASE = """You are FloatChat's SQL expert for the ARGO ocean float database.
Your sole job is to convert a user's natural-language question into a single valid PostgreSQL
SELECT statement.

=== DATABASE CONTEXT ===
{schema_context}

=== RULES ===
1. Output ONLY the raw SQL query — no explanation, no markdown, no backticks.
2. Always include LIMIT 5000 (the system will cap it regardless).
3. Only reference tables: float_metadata, profiles, trajectory_points, bgc_profiles.
4. Never use DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER, or any DDL/DML.
5. Use aliases: fm=float_metadata, p=profiles, tp=trajectory_points, b=bgc_profiles.
6. When the user asks about a region (e.g. "Arabian Sea", "Bay of Bengal"), use these bounding
   boxes:
     Arabian Sea: lat 5–25, lon 55–77
     Bay of Bengal: lat 5–22, lon 80–98
     Indian Ocean: lat -60–30, lon 20–120
7. "Sea surface" means pressure BETWEEN 0 AND 10 (dbar ≈ meters).
8. Default to the last 3 years if no date range is specified.
9. Return NULL / IS NOT NULL safe queries for BGC columns (many rows will be NULL).
10. Do NOT invent column names — refer only to the schema above.
"""

SUMMARY_SYSTEM_PROMPT = """You are FloatChat, a friendly oceanography assistant.
The user asked: {question}

A database query returned these results (first rows shown):
{results_preview}

Write a concise, clear 2–4 sentence summary of these results for a {mode} audience.
- Citizen mode: use plain language, no jargon, highlight the key finding.
- Researcher mode: include exact values, QC context, caveats about data coverage.
Respond in {language}.
"""


def build_sql_prompt(user_question: str, schema_context: str) -> list[dict]:
    """Return the messages list for the Claude API call."""
    system = SYSTEM_PROMPT_BASE.format(schema_context=schema_context)
    return [
        {"role": "user", "content": user_question}
    ], system


def build_summary_prompt(
    question: str,
    results_preview: str,
    mode: str = "citizen",
    language: str = "English",
) -> list[dict]:
    system = SUMMARY_SYSTEM_PROMPT.format(
        question=question,
        results_preview=results_preview,
        mode=mode,
        language=language,
    )
    return [{"role": "user", "content": "Summarise the results."}], system