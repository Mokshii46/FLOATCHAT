"""
Explainability service — USP 5.

Packages the generated SQL, routing decision, RAG context chunks, and
reasoning steps into a structured dict for display in ExplainabilityPanel.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ExplainabilityPayload:
    source: str             # "template" | "llm"
    template_id: str | None # template ID if template matched
    template_description: str | None
    params_used: dict | None
    sql: str
    rag_context_snippet: str   # first 500 chars of RAG context injected
    reasoning: str              # short explanation for the user


def build_payload(
    route_result: dict,
    rag_context: str = "",
) -> dict[str, Any]:
    """
    Build an explainability payload from router output.

    Parameters
    ----------
    route_result : dict returned by nl2sql.router.route()
    rag_context  : RAG context string injected into the LLM prompt (if LLM path)
    """
    source = route_result.get("source", "unknown")
    tmpl = route_result.get("template")
    params = route_result.get("params")
    sql = route_result.get("sql", "")

    if source == "template":
        reasoning = (
            f"Your question matched the pre-built template "
            f"'{tmpl['id'] if tmpl else '?'}' — "
            f"'{tmpl['description'] if tmpl else ''}'. "
            f"Parameters were extracted from your question: {params}. "
            f"No LLM call was made for this query."
        )
        template_id = tmpl["id"] if tmpl else None
        template_description = tmpl["description"] if tmpl else None
    else:
        reasoning = (
            "No pre-built template matched your question. "
            "The system retrieved relevant schema context from the vector store "
            "and asked the LLM to generate a SQL query. "
            "The generated SQL was validated before execution."
        )
        template_id = None
        template_description = None

    payload = ExplainabilityPayload(
        source=source,
        template_id=template_id,
        template_description=template_description,
        params_used=params,
        sql=sql,
        rag_context_snippet=rag_context[:500] if rag_context else "",
        reasoning=reasoning,
    )
    return asdict(payload)
