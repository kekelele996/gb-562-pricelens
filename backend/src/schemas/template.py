from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FieldRule(BaseModel):
    field: str
    label: str
    type: str
    selector_candidates: list[str]
    post_regex: str | None = None
    verified_value: str | None = None
    anchor_text: str | None = None
    patched: bool | None = None
    patch_note: str | None = None


class TemplateOut(BaseModel):
    id: int
    site_id: int
    site_name: str
    name: str
    version: int
    status: str
    coverage_score: float
    field_count: int
    last_verified_at: datetime | None
    change_note: str | None
    field_rules: list[dict[str, Any]]


class TemplatePatchIn(BaseModel):
    field_rules: list[FieldRule]
    change_note: str | None = None


class PreviewField(BaseModel):
    field: str
    label: str
    type: str
    value: str | None
    status: str
    matched_selector: str | None
    snippet: str | None


class PreviewOut(BaseModel):
    template_id: int
    template_version: int
    snapshot_id: int
    snapshot_label: str
    hits: int
    total: int
    fields: list[PreviewField]
