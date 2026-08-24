"""
Explainability service — USP 5.

Packages the generated SQL, routing decision, RAG context chunks,
academic provenance (PI, project, DAC), and reasoning steps into
a structured dict for display in ExplainabilityPanel and researcher mode.
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
    provenance: dict | None = None


def resolve_provenance(route_result: dict, rows: list[dict] | None = None) -> dict:
    """Extract academic provenance: PI name, Project, DAC, and Platform."""
    wmo_id = None
    if route_result.get("params") and "wmo_id" in route_result["params"]:
        wmo_id = route_result["params"]["wmo_id"]
    elif rows and len(rows) > 0 and "wmo_id" in rows[0]:
        wmo_id = str(rows[0]["wmo_id"])

    pi_name = None
    project_name = None
    dac = None
    platform_type = None

    if wmo_id:
        from services.query_service import execute_query
        try:
            meta = execute_query(
                f"SELECT pi_name, project_name, dac, platform_type FROM float_metadata WHERE wmo_id = '{wmo_id}' LIMIT 1"
            )
            if meta:
                pi_name = meta[0].get("pi_name")
                project_name = meta[0].get("project_name")
                dac = meta[0].get("dac")
                platform_type = meta[0].get("platform_type")
        except Exception:
            pass

    return {
        "pi_name": pi_name or "Dr. M. Ravichandran / International ARGO PIs",
        "project_name": project_name or "Indian Argo Project / Global ARGO Program",
        "dac": (dac.upper() if dac else "INCOIS / GDAC"),
        "platform_type": platform_type or "APEX / PROVOR / NAVIS",
        "citation": "Data collected and freely distributed by the International Argo Program (https://argo.ucsd.edu).",
    }


def build_payload(
    route_result: dict,
    rag_context: str = "",
    rows: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Build an explainability payload from router output with academic provenance.

    Parameters
    ----------
    route_result : dict returned by nl2sql.router.route()
    rag_context  : RAG context string injected into the LLM prompt (if LLM path)
    rows         : Query result rows (to extract specific float provenance)
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

    provenance = resolve_provenance(route_result, rows)

    payload = ExplainabilityPayload(
        source=source,
        template_id=template_id,
        template_description=template_description,
        params_used=params,
        sql=sql,
        rag_context_snippet=rag_context[:500] if rag_context else "",
        reasoning=reasoning,
        provenance=provenance,
    )
    return asdict(payload)
