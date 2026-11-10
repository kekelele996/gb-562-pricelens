from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base
from src.utils.timeutil import utcnow


class DriftAlert(Base):
    __tablename__ = "drift_alerts"
    __table_args__ = (UniqueConstraint("site_id", "snapshot_id", name="uq_alert_snapshot"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("snapshots.id"), index=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("extraction_templates.id"), nullable=True)
    drift_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    diagnosis: Mapped[dict] = mapped_column(JSON)
    suggested_patch: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    handled_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    handle_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
