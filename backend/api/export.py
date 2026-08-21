"""
GET /export/csv — export the last query result as a CSV download.

The caller passes the same SQL used by the chat endpoint.
"""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from nl2sql.sql_validator import validate, SQLValidationError
from services.query_service import execute_query

router = APIRouter()


@router.get("/csv")
def export_csv(
    sql: str = Query(..., description="Validated SELECT SQL to export"),
    filename: str = Query("floatchat_export.csv"),
):
    try:
        validated = validate(sql)
    except SQLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        rows = execute_query(validated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        raise HTTPException(status_code=204, detail="No data to export.")

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    for row in rows:
        # Serialise datetime
        writer.writerow({
            k: (v.isoformat() if hasattr(v, "isoformat") else v)
            for k, v in row.items()
        })

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
