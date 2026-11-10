"""模板读取 / 编辑 / 快照预览 / 自愈版本生成。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.constants.enums import TemplateStatus
from src.models.site import Site
from src.models.snapshot import Snapshot
from src.models.template import ExtractionTemplate
from src.services import extraction_service
from src.utils.timeutil import iso_utc, utcnow


def serialize_template(db: Session, template: ExtractionTemplate) -> dict:
    site = db.get(Site, template.site_id)
    return {
        "id": template.id,
        "site_id": template.site_id,
        "site_name": site.name if site else "",
        "name": template.name,
        "version": template.version,
        "status": template.status,
        "coverage_score": round(template.coverage_score, 4),
        "field_count": len(template.field_rules or []),
        "last_verified_at": iso_utc(template.last_verified_at),
        "change_note": template.change_note,
        "field_rules": template.field_rules or [],
    }


def get_template(db: Session, template_id: int) -> ExtractionTemplate | None:
    return db.get(ExtractionTemplate, template_id)


def update_rules(db: Session, template: ExtractionTemplate, field_rules: list[dict], change_note: str | None) -> ExtractionTemplate:
    template.field_rules = field_rules
    template.coverage_score = round(len([r for r in field_rules if r.get("verified_value")]) / max(len(field_rules), 1), 4)
    template.change_note = change_note or template.change_note
    template.last_verified_at = utcnow()
    return template


def preview(db: Session, template: ExtractionTemplate, snapshot_id: int | None) -> dict:
    snapshot = None
    if snapshot_id:
        snapshot = db.get(Snapshot, snapshot_id)
    if snapshot is None:
        baseline = db.scalars(
            select(Snapshot).where(Snapshot.site_id == template.site_id, Snapshot.is_baseline.is_(True))
        ).first()
        snapshot = baseline or db.scalars(
            select(Snapshot).where(Snapshot.site_id == template.site_id).order_by(desc(Snapshot.captured_at))
        ).first()
    if snapshot is None:
        raise ValueError("snapshot_not_found")
    results, _ = extraction_service.extract_document(snapshot.html, template.field_rules or [])
    hits = sum(1 for r in results if r["status"] == "hit")
    return {
        "template_id": template.id,
        "template_version": template.version,
        "snapshot_id": snapshot.id,
        "snapshot_label": snapshot.label,
        "hits": hits,
        "total": len(results),
        "fields": results,
    }


def active_template_for_site(db: Session, site_id: int) -> ExtractionTemplate | None:
    return db.scalars(
        select(ExtractionTemplate)
        .where(ExtractionTemplate.site_id == site_id, ExtractionTemplate.status == TemplateStatus.ACTIVE.value)
        .order_by(desc(ExtractionTemplate.version))
    ).first()


def create_version_from_patch(
    db: Session,
    base: ExtractionTemplate,
    patch: dict[str, str],
    note: str,
    actor: str,
) -> ExtractionTemplate:
    from src.services.selector_healer import apply_patch

    new_rules = apply_patch(base.field_rules or [], patch, note)
    version = base.version + 1
    template = ExtractionTemplate(
        site_id=base.site_id,
        name=base.name,
        version=version,
        status=TemplateStatus.ACTIVE.value,
        field_rules=new_rules,
        coverage_score=min(1.0, base.coverage_score + 0.1),
        last_verified_at=utcnow(),
        change_note=f"{note}（{actor}）",
    )
    base.status = TemplateStatus.DEPRECATED.value
    db.add(template)
    db.flush()
    return template
