"""
Builds the prompt sent to the LLM for freeform NL2SQL (used only when
router.py finds no template match). Keeps the system prompt strict about
output format so query_generator.py can parse it reliably, and injects
schema context retrieved from the vector store so the model can't
hallucinate column names.
"""

from __future__ import annotations

from config import settings

SYSTEM_PROMPT = """You are a PostgreSQL query generator for FloatChat, a system that answers \
questions about ARGO ocean float data. You are given schema documentation for the relevant \
tables and a user's natural-language question. Your job is to output ONE valid, read-only \
PostgreSQL SELECT statement that answers it.

Rules:
- Output ONLY the SQL statement. No explanation, no markdown code fences, no commentary.
- SELECT statements only. Never write INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, \
or any other write/DDL statement.
- Only use tables and columns that appear in the provided schema context. Never invent a \
column name.
- Always join through float_metadata.id (not wmo_id directly) when filtering by a float's \
WMO id.
- Always include an explicit LIMIT clause. If the question doesn't imply a specific row \
count, use LIMIT {max_rows}.
- Use PostGIS functions (ST_Within, ST_DWithin, ST_MakeEnvelope) for spatial filters when a \
geometry column is available, or plain lat/lon BETWEEN filters otherwise.
- If the question cannot be answered with the given schema, output exactly: \
SELECT 'unanswerable' AS error LIMIT 1
"""

FEW_SHOT_EXAMPLES = [
    (
        "What was the average salinity in the Arabian Sea in March 2023?",
        """SELECT AVG(p.salinity) AS avg_salinity, COUNT(*) AS n_obs
FROM profiles p
WHERE p.lon BETWEEN 50 AND 78
  AND p.lat BETWEEN 5 AND 25
  AND p.timestamp BETWEEN '2023-03-01' AND '2023-04-01'
LIMIT 5000;""",
    ),
    (
        "Which floats are currently active?",
        """SELECT wmo_id, platform_type, dac
FROM float_metadata
WHERE status = 'active'
ORDER BY wmo_id
LIMIT 5000;""",
    ),
    (
        "Show me the chlorophyll trend for BGC floats near the equator in 2022.",
        """SELECT date_trunc('month', b.timestamp) AS month, AVG(b.chlorophyll) AS avg_chlorophyll
FROM bgc_profiles b
JOIN float_metadata fm ON fm.id = b.float_id
WHERE fm.is_bgc = TRUE
  AND b.lat BETWEEN -5 AND 5
  AND b.timestamp BETWEEN '2022-01-01' AND '2023-01-01'
GROUP BY 1
ORDER BY 1
LIMIT 5000;""",
    ),
]


def build_prompt(question: str, schema_context: str) -> list[dict]:
    """Returns the `messages` list ready to pass to the Anthropic API."""
    examples_text = "\n\n".join(
        f"Question: {q}\nSQL:\n{sql}" for q, sql in FEW_SHOT_EXAMPLES
    )

    user_content = f"""Schema context:
{schema_context}

Examples:
{examples_text}

Question: {question}
SQL:"""

    return [{"role": "user", "content": user_content}]


def build_system_prompt() -> str:
    return SYSTEM_PROMPT.format(max_rows=settings.max_result_rows)