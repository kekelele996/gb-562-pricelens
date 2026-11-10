"""批次控制器。"""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from src.services import audit_service, run_service, snapshot_service, template_service
from src.utils.errors import AppError


def list_runs(db: Session, site_id: int | None) -> dict:
    return run_service.list_runs(db, site_id)


def get_run(db: Session, run_id: int) -> dict:
    run = run_service.get_run(db, run_id)
    if run is None:
        raise AppError("NOT_FOUND", 404)
    return run_service.serialize_run(db, run)


def execute(db: Session, principal, payload: dict, request: Request) -> dict:
    template = template_service.get_template(db, payload["template_id"])
    snapshot = snapshot_service.get_snapshot(db, payload["snapshot_id"])
    if template is None or snapshot is None:
        raise AppError("NOT_FOUND", 404)
    if template.site_id != snapshot.site_id:
        raise AppError("CONFLICT", 409, detail="template_site_mismatch")
    run = run_service.execute_run(db, template, snapshot, triggered_by=principal.email)
    audit_service.record(
        db,
        actor_email=principal.email,
        actor_role=principal.role,
        action="run.execute",
        entity="run",
        entity_id=run.id,
        detail={
            "template_id": template.id,
            "version": template.version,
            "snapshot_id": snapshot.id,
            "f1_score": run.f1_score,
            "status": run.status,
        },
        ip=request.client.host if request.client else None,
    )
    db.commit()
    return run_service.serialize_run(db, run)
