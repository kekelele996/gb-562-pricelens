from __future__ import annotations

from pydantic import BaseModel


class ReportRow(BaseModel):
    site_id: int
    site_name: str
    domain: str
    snapshot_label: str
    captured_at: str
    title: str | None
    list_price: str | None
    promo_price: str | None
    stock: str | None
    f1_score: float | None
    status: str


class ReportOut(BaseModel):
    generated_at: str
    rows: list[ReportRow]
    avg_f1: float | None
