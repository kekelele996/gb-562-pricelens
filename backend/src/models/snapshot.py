from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base
from src.utils.timeutil import utcnow


class Snapshot(Base):
    __tablename__ = "snapshots"
    __table_args__ = (UniqueConstraint("site_id", "dom_hash", name="uq_snapshot_dom"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    url: Mapped[str] = mapped_column(String(400))
    label: Mapped[str] = mapped_column(String(80), default="daily")
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    html: Mapped[str] = mapped_column(Text)
    dom_hash: Mapped[str] = mapped_column(String(64), index=True)
    byte_size: Mapped[int] = mapped_column(Integer, default=0)
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False)
