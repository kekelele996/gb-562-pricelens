"""告警控制器。"""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from src.services import alert_service, audit_service
from src.services.snapshot_service import serialize_alert
from src.utils.errors import AppError


def list_alerts(db: Session, status: str | None) -> dict:
    return alert_service.list_alerts(db, status)


def get_alert(db: Session, alert_id: int) -> dict:
    alert = alert_service.get_alert(db, alert_id)
    if alert is None:
        raise AppError("NOT_FOUND", 404)
    return serialize_alert(db, alert)


def recompute_candidates(db: Session, alert_id: int, principal, request: Request) -> dict:
    alert = alert_service.get_alert(db, alert_id)
    if alert is None:
        raise AppError("NOT_FOUND", 404)
    try:
        patch = alert_service.recompute_candidates(db, alert)
    except ValueError as exc:
        raise AppError("CONFLICT", 409, detail=str(exc)) from exc
    db.commit()
    return {"alert": serialize_alert(db, alert), "suggested_patch": patch}


def change_status(db: Session, alert_id: int, principal, payload: dict, request: Request) -> dict:
    alert = alert_service.get_alert(db, alert_id)
    if alert is None:
        raise AppError("NOT_FOUND", 404)
    try:
        alert_service.change_status(db, alert, payload["status"], payload.get("note"), principal.email)
    except ValueError as exc:
        raise AppError("VALIDATION", 422, detail=str(exc)) from exc
    audit_service.record(
        db,
        actor_email=principal.email,
        actor_role=principal.role,
        action=f"alert.{payload['status']}",
        entity="alert",
        entity_id=alert.id,
        detail={"severity": alert.severity, "drift_score": alert.drift_score, "note": payload.get("note")},
        ip=request.client.host if request.client else None,
    )
    db.commit()
    return {"id": alert.id, "status": alert.status, "audit_added": 2}


def apply_patch(db: Session, alert_id: int, principal, request: Request) -> dict:
    from src.services.template_service import serialize_template

    alert = alert_service.get_alert(db, alert_id)
    if alert is None:
        raise AppError("NOT_FOUND", 404)
    try:
        template = alert_service.apply_patch_to_template(db, alert, principal.email)
    except ValueError as exc:
        raise AppError("CONFLICT", 409, detail=str(exc)) from exc
    audit_service.record(
        db,
        actor_email=principal.email,
        actor_role=principal.role,
        action="template.apply_patch",
        entity="template",
        entity_id=template.id,
        detail={"source_alert": alert.id, "version": template.version, "patch": alert.suggested_patch.get("patch", {})},
        ip=request.client.host if request.client else None,
    )
    db.commit()
    return {
        "template": serialize_template(db, template),
        "source_alert": alert.id,
        "audit_added": 2,
    }
