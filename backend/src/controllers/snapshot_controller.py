"""快照与诊断控制器。"""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from src.services import audit_service, snapshot_service, template_service
from src.utils.errors import AppError


def list_snapshots(db: Session, site_id: int | None) -> dict:
    items = snapshot_service.list_snapshots(db, site_id)
    return {"items": items, "total": len(items)}


def get_snapshot(db: Session, snapshot_id: int) -> dict:
    snapshot = snapshot_service.get_snapshot(db, snapshot_id)
    if snapshot is None:
        raise AppError("NOT_FOUND", 404)
    data = snapshot_service.serialize_snapshot(db, snapshot)
    baseline = snapshot_service.baseline_for(db, snapshot.site_id, exclude_id=snapshot.id)
    data["baseline"] = snapshot_service.serialize_snapshot(db, baseline) if baseline else None
    return data


def diagnose(db: Session, snapshot_id: int, template_id: int, principal, request: Request) -> dict:
    snapshot = snapshot_service.get_snapshot(db, snapshot_id)
    if snapshot is None:
        raise AppError("NOT_FOUND", 404)
    template = template_service.get_template(db, template_id)
    if template is None or template.site_id != snapshot.site_id:
        raise AppError("CONFLICT", 409, detail="template_site_mismatch")
    alert = snapshot_service.upsert_alert(db, snapshot, template)
    audit_service.record(
        db,
        actor_email=principal.email,
        actor_role=principal.role,
        action="diagnose.run",
        entity="snapshot",
        entity_id=snapshot.id,
        detail={
            "template_id": template.id,
            "drift_score": alert.drift_score,
            "severity": alert.severity,
        },
        ip=request.client.host if request.client else None,
    )
    db.commit()
    return snapshot_service.serialize_alert(db, alert)
