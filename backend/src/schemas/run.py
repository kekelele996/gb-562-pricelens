from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RunCreateIn(BaseModel):
    template_id: int
    snapshot_id: int


class FieldResult(BaseModel):
    field: str
    label: str
    type: str
    value: str | None
    raw: str | None
    status: str
    similarity: float
    matched_selector: str | None
    snippet: str | None


class RunOut(BaseModel):
    id: int
    template_id: int
    template_name: str
    template_version: int
    site_id: int
    site_name: str
    snapshot_id: int
    status: str
    hit_fields: int
    missing_fields: int
    f1_score: float | None
    duration_ms: int
    triggered_by: str
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
    field_results: list[dict[str, Any]]


class RunListOut(BaseModel):
    items: list[RunOut]
    total: int
    trend: list[dict[str, Any]]
