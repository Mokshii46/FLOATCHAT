"""
GET /floats          — list of all floats (with optional filters)
GET /floats/{wmo_id} — single float detail + latest trajectory + prediction
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any

from database import SessionLocal
from models.float_metadata import FloatMetadata
from models.trajectory import TrajectoryPoint
from services.trajectory_predictor import predict_next_position

router = APIRouter()


class FloatSummary(BaseModel):
    wmo_id: str
    dac: str | None
    platform_type: str | None
    deploy_date: str | None
    deploy_lat: float | None
    deploy_lon: float | None
    is_bgc: bool
    status: str | None


class FloatDetail(FloatSummary):
    latest_cycle: int | None
    latest_lat: float | None
    latest_lon: float | None
    latest_timestamp: str | None
    predicted_next_lat: float | None
    predicted_next_lon: float | None
    prediction_confidence: float | None


@router.get("", response_model=list[FloatSummary])
def list_floats(
    status: str = Query("active"),
    is_bgc: bool | None = Query(None),
    limit: int = Query(200, le=1000),
):
    db = SessionLocal()
    try:
        q = db.query(FloatMetadata).filter(FloatMetadata.status == status)
        if is_bgc is not None:
            q = q.filter(FloatMetadata.is_bgc == is_bgc)
        floats = q.limit(limit).all()
        return [
            FloatSummary(
                wmo_id=f.wmo_id,
                dac=f.dac,
                platform_type=f.platform_type,
                deploy_date=f.deploy_date.isoformat() if f.deploy_date else None,
                deploy_lat=f.deploy_lat,
                deploy_lon=f.deploy_lon,
                is_bgc=f.is_bgc,
                status=f.status,
            )
            for f in floats
        ]
    finally:
        db.close()


@router.get("/{wmo_id}", response_model=FloatDetail)
def get_float(wmo_id: str):
    db = SessionLocal()
    try:
        fm = db.query(FloatMetadata).filter_by(wmo_id=wmo_id).first()
        if fm is None:
            raise HTTPException(status_code=404, detail=f"Float {wmo_id} not found.")

        latest_tp = (
            db.query(TrajectoryPoint)
            .filter_by(float_id=fm.id)
            .order_by(TrajectoryPoint.cycle_number.desc())
            .first()
        )

        # Trigger trajectory prediction (fast, uses cached if already exists)
        pred = predict_next_position(wmo_id)

        return FloatDetail(
            wmo_id=fm.wmo_id,
            dac=fm.dac,
            platform_type=fm.platform_type,
            deploy_date=fm.deploy_date.isoformat() if fm.deploy_date else None,
            deploy_lat=fm.deploy_lat,
            deploy_lon=fm.deploy_lon,
            is_bgc=fm.is_bgc,
            status=fm.status,
            latest_cycle=latest_tp.cycle_number if latest_tp else None,
            latest_lat=latest_tp.lat if latest_tp else None,
            latest_lon=latest_tp.lon if latest_tp else None,
            latest_timestamp=latest_tp.timestamp.isoformat() if latest_tp and latest_tp.timestamp else None,
            predicted_next_lat=pred.next_lat if pred else None,
            predicted_next_lon=pred.next_lon if pred else None,
            prediction_confidence=pred.confidence if pred else None,
        )
    finally:
        db.close()
