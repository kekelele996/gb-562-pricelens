from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditOut(BaseModel):
    id: int
    actor_email: str
    actor_role: str
    action: str
    entity: str
    entity_id: str | None
    detail: dict[str, Any]
    layer: str
    created_at: datetime


class AuditListOut(BaseModel):
    items: list[AuditOut]
    total: int
