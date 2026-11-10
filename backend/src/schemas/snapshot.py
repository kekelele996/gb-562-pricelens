from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SnapshotOut(BaseModel):
    id: int
    site_id: int
    site_name: str
    url: str
    label: str
    captured_at: datetime
    dom_hash: str
    byte_size: int
    is_baseline: bool


class DiagnoseIn(BaseModel):
    template_id: int


class AlertOut(BaseModel):
    id: int
    site_id: int
    site_name: str
    snapshot_id: int
    template_id: int | None
    template_name: str | None
    drift_score: float
    severity: str
    status: str
    handled_by: str | None
    handle_note: str | None
    created_at: datetime
    diagnosis: dict[str, Any]
    suggested_patch: dict[str, Any]


class AlertListOut(BaseModel):
    items: list[AlertOut]
    total: int
    open_count: int


class AlertStatusIn(BaseModel):
    status: str = Field(pattern="^(accepted|dismissed)$")
    note: str | None = None


class AlertStatusOut(BaseModel):
    id: int
    status: str
    audit_added: int
