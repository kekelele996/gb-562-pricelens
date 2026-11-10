from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base
from src.utils.timeutil import utcnow


class ExtractionRun(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("extraction_templates.id"), index=True)
    template_version: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("snapshots.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    field_results: Mapped[list] = mapped_column(JSON)
    hit_fields: Mapped[int] = mapped_column(Integer, default=0)
    missing_fields: Mapped[int] = mapped_column(Integer, default=0)
    f1_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    triggered_by: Mapped[str] = mapped_column(String(160), default="seed")
    seed_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
