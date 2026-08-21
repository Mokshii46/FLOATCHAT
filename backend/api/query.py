"""
POST /query — raw structured query endpoint (for debugging / researcher mode).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nl2sql.sql_validator import validate, SQLValidationError
from services.query_service import execute_query

router = APIRouter()


class QueryRequest(BaseModel):
    sql: str = Field(..., description="Raw SQL SELECT statement to execute.")


class QueryResponse(BaseModel):
    rows: list[dict[str, Any]]
    row_count: int
    validated_sql: str


@router.post("", response_model=QueryResponse)
def raw_query(req: QueryRequest) -> QueryResponse:
    try:
        validated = validate(req.sql)
    except SQLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        rows = execute_query(validated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")

    return QueryResponse(rows=rows, row_count=len(rows), validated_sql=validated)
