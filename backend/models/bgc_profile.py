"""
BGC (bio-geochemical) profile rows — only populated for floats where
FloatMetadata.is_bgc is True. Parsed from *_Sprof.nc files (see
etl/parse_netcdf.py). Backs USP 7.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, DateTime, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class BGCProfile(Base):
    __tablename__ = "bgc_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    float_id: Mapped[int] = mapped_column(ForeignKey("float_metadata.id"), nullable=False, index=True)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    lat: Mapped[float] = mapped_column(nullable=False)
    lon: Mapped[float] = mapped_column(nullable=False)
    pressure: Mapped[float] = mapped_column(nullable=False)

    dissolved_oxygen: Mapped[float] = mapped_column(nullable=True)     # umol/kg
    chlorophyll: Mapped[float] = mapped_column(nullable=True)          # mg/m3
    ph: Mapped[float] = mapped_column(nullable=True)                   # total scale
    nitrate: Mapped[float] = mapped_column(nullable=True)              # umol/kg
    backscatter: Mapped[float] = mapped_column(nullable=True)          # m-1

    dissolved_oxygen_qc: Mapped[str] = mapped_column(String(2), nullable=True)
    chlorophyll_qc: Mapped[str] = mapped_column(String(2), nullable=True)
    ph_qc: Mapped[str] = mapped_column(String(2), nullable=True)
    nitrate_qc: Mapped[str] = mapped_column(String(2), nullable=True)

    float_ = relationship("FloatMetadata", back_populates="bgc_profiles")

    __table_args__ = (
        Index("ix_bgc_float_cycle", "float_id", "cycle_number"),
    )

    def __repr__(self) -> str:
        return f"<BGCProfile float_id={self.float_id} cycle={self.cycle_number}>"