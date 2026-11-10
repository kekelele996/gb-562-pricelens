"""告警队列：候选重算 / 处置 / 一键应用生成模板新版本。"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.constants.enums import AlertStatus
from src.models.alert import DriftAlert
from src.models.site import Site
from src.models.snapshot import Snapshot
from src.models.template import ExtractionTemplate
from src.services import run_service
from src.services.snapshot_service import serialize_alert
from src.services.template_service import create_version_from_patch
from src.utils.timeutil import utcnow


def list_alerts(db: Session, status: str | None = None) -> dict:
    stmt = select(DriftAlert).order_by(DriftAlert.drift_score.desc(), DriftAlert.id.desc())
    if status:
        stmt = stmt.where(DriftAlert.status == status)
    alerts = db.scalars(stmt).all()
    open_count = db.scalar(
        select(func.count()).select_from(DriftAlert).where(DriftAlert.status == AlertStatus.OPEN.value)
    ) or 0
    return {
        "items": [serialize_alert(db, a) for a in alerts],
        "total": len(alerts),
        "open_count": open_count,
    }


def get_alert(db: Session, alert_id: int) -> DriftAlert | None:
    return db.get(DriftAlert, alert_id)


def recompute_candidates(db: Session, alert: DriftAlert) -> dict:
    from src.services import selector_healer

    snapshot = db.get(Snapshot, alert.snapshot_id)
    template = db.get(ExtractionTemplate, alert.template_id) if alert.template_id else None
    if snapshot is None or template is None:
        raise ValueError("alert_context_missing")
    stability = run_service.stability_map(db, alert.site_id, template.field_rules or [])
    counts = run_service.history_counts(db, alert.site_id, template.field_rules or [])
    healing = selector_healer.heal(snapshot.html, template.field_rules or [], stability, counts)
    alert.suggested_patch = {
        "patch": healing["suggested_patch"],
        "fields": healing["fields"],
        "threshold": healing["threshold"],
        "auto_apply_count": healing["auto_apply_count"],
    }
    alert.updated_at = utcnow()
    db.flush()
    return alert.suggested_patch


def change_status(db: Session, alert: DriftAlert, status: str, note: str | None, actor_email: str) -> DriftAlert:
    if status not in {AlertStatus.ACCEPTED.value, AlertStatus.DISMISSED.value}:
        raise ValueError("invalid_status")
    alert.status = status
    alert.handled_by = actor_email
    alert.handle_note = note
    alert.updated_at = utcnow()
    db.flush()
    return alert


def apply_patch_to_template(db: Session, alert: DriftAlert, actor_email: str) -> ExtractionTemplate:
    snapshot = db.get(Snapshot, alert.snapshot_id)
    template = db.get(ExtractionTemplate, alert.template_id) if alert.template_id else None
    site = db.get(Site, alert.site_id)
    if snapshot is None or template is None or site is None:
        raise ValueError("alert_context_missing")
    patch = (alert.suggested_patch or {}).get("patch") or {}
    if not patch:
        raise ValueError("no_candidate")
    new_template = create_version_from_patch(
        db, template, patch, f"快照#{snapshot.id} 自愈应用", actor_email
    )
    # 快照记录一次真实复跑，便于页面直接对比 F1
    run_service.execute_run(
        db, new_template, snapshot, triggered_by=f"self-heal:{actor_email}", seed_key=None
    )
    db.flush()
    return new_template
