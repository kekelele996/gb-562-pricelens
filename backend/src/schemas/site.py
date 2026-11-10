from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SiteCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    domain: str = Field(min_length=4, max_length=160)
    market: str = Field(default="全国", max_length=40)
    robots_policy: str = Field(default="partial", pattern="^(allow|partial|blocked)$")
    qps_limit: float = Field(default=1.0, ge=0.1, le=20)
    status: str = Field(default="active", pattern="^(active|paused)$")
    note: str | None = None


class TemplateBrief(BaseModel):
    id: int
    name: str
    version: int
    status: str
    coverage_score: float
    field_count: int


class SiteOut(BaseModel):
    id: int
    name: str
    domain: str
    market: str
    robots_policy: str
    qps_limit: float
    status: str
    alert_count: int
    last_crawled_at: datetime | None
    templates: list[TemplateBrief]


class SiteListOut(BaseModel):
    items: list[SiteOut]
    total: int
