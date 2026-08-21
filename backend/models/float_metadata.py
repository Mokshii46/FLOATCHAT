"""One row per physical ARGO float."""

from datetime import date

from sqlalchemy import String, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class FloatMetadata(Base):
    __tablename__ = "float_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wmo_id: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    dac: Mapped[str] = mapped_column(String(32), nullable=True)               # e.g. "incois"
    platform_type: Mapped[str] = mapped_column(String(64), nullable=True)     # e.g. "APEX", "NOVA"
    project_name: Mapped[str] = mapped_column(String(128), nullable=True)
    pi_name: Mapped[str] = mapped_column(String(128), nullable=True)
    deploy_date: Mapped[date] = mapped_column(Date, nullable=True)
    deploy_lat: Mapped[float] = mapped_column(nullable=True)
    deploy_lon: Mapped[float] = mapped_column(nullable=True)
    is_bgc: Mapped[bool] = mapped_column(default=False)                       # feeds USP 7 routing
    status: Mapped[str] = mapped_column(String(16), default="active")         # active | dead | unknown

    profiles = relationship("Profile", back_populates="float_", cascade="all, delete-orphan")
    trajectory_points = relationship("TrajectoryPoint", back_populates="float_", cascade="all, delete-orphan")
    bgc_profiles = relationship("BGCProfile", back_populates="float_", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FloatMetadata wmo_id={self.wmo_id} bgc={self.is_bgc}>"