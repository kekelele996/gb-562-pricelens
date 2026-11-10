from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base
from src.utils.timeutil import utcnow


class ExtractionTemplate(Base):
    __tablename__ = "extraction_templates"
    __table_args__ = (UniqueConstraint("site_id", "name", "version", name="uq_template_version"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    field_rules: Mapped[list] = mapped_column(JSON)
    coverage_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    change_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
