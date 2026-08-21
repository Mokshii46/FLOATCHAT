"""
Core physical profile: one row per (float, cycle, pressure level).
This is the main table NL2SQL queries hit for temperature/salinity questions.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    float_id: Mapped[int] = mapped_column(ForeignKey("float_metadata.id"), nullable=False, index=True)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    lat: Mapped[float] = mapped_column(nullable=False)
    lon: Mapped[float] = mapped_column(nullable=False)
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    pressure: Mapped[float] = mapped_column(nullable=False)          # dbar (proxy for depth)
    temperature: Mapped[float] = mapped_column(nullable=True)        # degC
    salinity: Mapped[float] = mapped_column(nullable=True)           # PSU

    pressure_qc: Mapped[str] = mapped_column(String(2), nullable=True)
    temperature_qc: Mapped[str] = mapped_column(String(2), nullable=True)
    salinity_qc: Mapped[str] = mapped_column(String(2), nullable=True)

    float_ = relationship("FloatMetadata", back_populates="profiles")

    __table_args__ = (
        Index("ix_profiles_float_cycle", "float_id", "cycle_number"),
        Index("ix_profiles_timestamp_pressure", "timestamp", "pressure"),
    )

    def __repr__(self) -> str:
        return f"<Profile float_id={self.float_id} cycle={self.cycle_number} p={self.pressure}>"