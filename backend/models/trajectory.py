"""
One row per cycle's surfacing position (lat/lon/time), independent of the
per-pressure-level Profile rows. This is what map/trajectory rendering and
the USP 3 trajectory predictor read from — much cheaper to scan than
joining through every pressure level in `profiles`.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from database import Base


class TrajectoryPoint(Base):
    __tablename__ = "trajectory_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    float_id: Mapped[int] = mapped_column(ForeignKey("float_metadata.id"), nullable=False, index=True)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    lat: Mapped[float] = mapped_column(nullable=False)
    lon: Mapped[float] = mapped_column(nullable=False)
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    # Filled in lazily by ml/trajectory_model.py for the most recent cycle only
    predicted_next_lat: Mapped[float] = mapped_column(nullable=True)
    predicted_next_lon: Mapped[float] = mapped_column(nullable=True)
    prediction_confidence: Mapped[float] = mapped_column(nullable=True)  # 0-1

    float_ = relationship("FloatMetadata", back_populates="trajectory_points")

    __table_args__ = (
        Index("ix_traj_float_cycle", "float_id", "cycle_number", unique=True),
    )

    def __repr__(self) -> str:
        return f"<TrajectoryPoint float_id={self.float_id} cycle={self.cycle_number}>"