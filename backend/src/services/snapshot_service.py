"""快照读取与漂移诊断落库。"""
from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.constants.enums import AlertStatus
from src.models.alert import DriftAlert
from src.models.site import Site
from src.models.snapshot import Snapshot
from src.models.template import ExtractionTemplate
from src.services import drift_detector, run_service, selector_healer
from src.utils.timeutil import iso_utc, utcnow


def serialize_snapshot(db: Session, snapshot: Snapshot) -> dict:
    site = db.get(Site, snapshot.site_id)
    return {
        "id": snapshot.id,
        "site_id": snapshot.site_id,
        "site_name": site.name if site else "",
        "domain": site.domain if site else "",
        "url": snapshot.url,
        "label": snapshot.label,
        "captured_at": iso_utc(snapshot.captured_at),
        "dom_hash": snapshot.dom_hash,
        "byte_size": snapshot.byte_size,
        "is_baseline": snapshot.is_baseline,
    }


def list_snapshots(db: Session, site_id: int | None = None, limit: int = 30) -> list[dict]:
    stmt = select(Snapshot).order_by(desc(Snapshot.captured_at)).limit(limit)
    if site_id:
        stmt = select(Snapshot).where(Snapshot.site_id == site_id).order_by(desc(Snapshot.captured_at)).limit(limit)
    return [serialize_snapshot(db, s) for s in db.scalars(stmt).all()]


def get_snapshot(db: Session, snapshot_id: int) -> Snapshot | None:
    return db.get(Snapshot, snapshot_id)


def baseline_for(db: Session, site_id: int, exclude_id: int | None = None) -> Snapshot | None:
    stmt = select(Snapshot).where(Snapshot.site_id == site_id, Snapshot.is_baseline.is_(True))
    if exclude_id:
        stmt = stmt.where(Snapshot.id != exclude_id)
    return db.scalars(stmt).first()


def build_diagnosis(db: Session, new_snapshot: Snapshot, template: ExtractionTemplate) -> tuple[dict, dict]:
    baseline = baseline_for(db, new_snapshot.site_id, exclude_id=new_snapshot.id)
    if baseline is None:
        base_html = new_snapshot.html
        basis = {"baseline_snapshot_id": new_snapshot.id, "baseline_missing": True}
    else:
        base_html = baseline.html
        basis = {"baseline_snapshot_id": baseline.id, "baseline_missing": False}
    diagnosis = drift_detector.diagnose(base_html, new_snapshot.html, template.field_rules or [])
    diagnosis.update(basis)
    stability = run_service.stability_map(db, new_snapshot.site_id, template.field_rules or [])
    counts = run_service.history_counts(db, new_snapshot.site_id, template.field_rules or [])
    healing = selector_healer.heal(new_snapshot.html, template.field_rules or [], stability, counts)
    patch = {
        "patch": healing["suggested_patch"],
        "fields": healing["fields"],
        "threshold": healing["threshold"],
        "auto_apply_count": healing["auto_apply_count"],
    }
    return diagnosis, patch


def upsert_alert(
    db: Session,
    new_snapshot: Snapshot,
    template: ExtractionTemplate,
    status: str | None = None,
) -> DriftAlert:
    diagnosis, patch = build_diagnosis(db, new_snapshot, template)
    alert = db.scalars(
        select(DriftAlert).where(
            DriftAlert.site_id == new_snapshot.site_id,
            DriftAlert.snapshot_id == new_snapshot.id,
        )
    ).first()
    created = alert is None
    if alert is None:
        alert = DriftAlert(
            site_id=new_snapshot.site_id,
            snapshot_id=new_snapshot.id,
            template_id=template.id,
            drift_score=diagnosis["drift_score"],
            severity=diagnosis["severity"],
            diagnosis=diagnosis,
            suggested_patch=patch,
            status=AlertStatus.OPEN.value,
        )
        db.add(alert)
    else:
        alert.drift_score = diagnosis["drift_score"]
        alert.severity = diagnosis["severity"]
        alert.diagnosis = diagnosis
        alert.suggested_patch = patch
        alert.template_id = template.id
        alert.updated_at = utcnow()
        if status:
            alert.status = status
    db.flush()
    return alert


def serialize_alert(db: Session, alert: DriftAlert) -> dict:
    site = db.get(Site, alert.site_id)
    template = db.get(ExtractionTemplate, alert.template_id) if alert.template_id else None
    return {
        "id": alert.id,
        "site_id": alert.site_id,
        "site_name": site.name if site else "",
        "snapshot_id": alert.snapshot_id,
        "template_id": alert.template_id,
        "template_name": template.name if template else None,
        "template_version": template.version if template else None,
        "drift_score": round(alert.drift_score, 4),
        "severity": alert.severity,
        "status": alert.status,
        "handled_by": alert.handled_by,
        "handle_note": alert.handle_note,
        "created_at": iso_utc(alert.created_at),
        "diagnosis": alert.diagnosis,
        "suggested_patch": alert.suggested_patch,
    }
