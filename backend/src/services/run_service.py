"""抽取批次执行 / 历史 / F1 趋势。"""
from __future__ import annotations

import time

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from src.constants.enums import RunStatus
from src.models.run import ExtractionRun
from src.models.site import Site
from src.models.snapshot import Snapshot
from src.models.template import ExtractionTemplate
from src.services import extraction_service
from src.utils.timeutil import iso_utc, utcnow


def serialize_run(db: Session, run: ExtractionRun) -> dict:
    template = db.get(ExtractionTemplate, run.template_id)
    snapshot = db.get(Snapshot, run.snapshot_id)
    site = db.get(Site, template.site_id) if template else None
    return {
        "id": run.id,
        "template_id": run.template_id,
        "template_name": template.name if template else "",
        "template_version": run.template_version,
        "site_id": site.id if site else 0,
        "site_name": site.name if site else "",
        "snapshot_id": run.snapshot_id,
        "snapshot_label": snapshot.label if snapshot else "",
        "status": run.status,
        "hit_fields": run.hit_fields,
        "missing_fields": run.missing_fields,
        "f1_score": round(run.f1_score, 4) if run.f1_score is not None else None,
        "duration_ms": run.duration_ms,
        "triggered_by": run.triggered_by,
        "started_at": iso_utc(run.started_at),
        "finished_at": iso_utc(run.finished_at),
        "error_message": run.error_message,
        "created_at": iso_utc(run.created_at),
        "field_results": run.field_results or [],
    }


def execute_run(
    db: Session,
    template: ExtractionTemplate,
    snapshot: Snapshot,
    triggered_by: str,
    seed_key: str | None = None,
    force_failed_reason: str | None = None,
) -> ExtractionRun:
    """同步执行一次抽取（毫秒级）；失败态也真实落库。"""
    started = utcnow()
    clock = time.perf_counter()
    run = ExtractionRun(
        template_id=template.id,
        template_version=template.version,
        snapshot_id=snapshot.id,
        status=RunStatus.RUNNING.value,
        field_results=[],
        triggered_by=triggered_by,
        seed_key=seed_key,
        started_at=started,
    )
    if force_failed_reason:
        run.status = RunStatus.FAILED.value
        run.field_results = []
        run.hit_fields = 0
        run.missing_fields = len(template.field_rules or [])
        run.duration_ms = 30000
        run.error_message = force_failed_reason
        run.finished_at = utcnow()
        db.add(run)
        db.flush()
        return run

    if snapshot.byte_size > 1_048_576:
        run.status = RunStatus.FAILED.value
        run.error_message = "snapshot_too_large(>1MB)"
        run.missing_fields = len(template.field_rules or [])
        run.finished_at = utcnow()
        db.add(run)
        db.flush()
        return run

    results, stats = extraction_service.extract_document(snapshot.html, template.field_rules or [])
    f1, detail = extraction_service.score_f1(results, len(template.field_rules or []))
    run.field_results = results
    run.hit_fields = sum(1 for r in results if r["status"] == "hit")
    run.missing_fields = sum(1 for r in results if r["status"] == "miss")
    run.f1_score = f1
    run.duration_ms = max(1, int((time.perf_counter() - clock) * 1000)) + 12
    run.finished_at = utcnow()
    if stats["extracted"] == 0:
        run.status = RunStatus.FAILED.value
        run.error_message = "all_fields_miss（页面无可解析商品节点）"
    else:
        run.status = RunStatus.SUCCESS.value
        run.error_message = None
    db.add(run)
    db.flush()
    return run


def get_run(db: Session, run_id: int) -> ExtractionRun | None:
    return db.get(ExtractionRun, run_id)


def list_runs(db: Session, site_id: int | None = None, limit: int = 40) -> dict:
    stmt = select(ExtractionRun).order_by(desc(ExtractionRun.id)).limit(limit)
    if site_id:
        template_ids = db.scalars(select(ExtractionTemplate.id).where(ExtractionTemplate.site_id == site_id)).all()
        if not template_ids:
            return {"items": [], "total": 0, "trend": []}
        stmt = (
            select(ExtractionRun)
            .where(ExtractionRun.template_id.in_(template_ids))
            .order_by(desc(ExtractionRun.id))
            .limit(limit)
        )
    runs = db.scalars(stmt).all()
    items = [serialize_run(db, run) for run in runs]
    total = db.scalar(select(func.count()).select_from(ExtractionRun)) or 0
    trend = [
        {
            "run_id": item["id"],
            "site_name": item["site_name"],
            "version": item["template_version"],
            "f1_score": item["f1_score"],
            "created_at": item["created_at"],
            "status": item["status"],
        }
        for item in sorted(items, key=lambda x: x["id"])
        if item["f1_score"] is not None
    ]
    return {"items": items, "total": total, "trend": trend}


def field_stability(db: Session, site_id: int, field: str) -> tuple[float, int]:
    """stability = 该站点该字段在历史批次中的正确率（跨模板版本）。"""
    runs = db.scalars(
        select(ExtractionRun)
        .join(ExtractionTemplate, ExtractionTemplate.id == ExtractionRun.template_id)
        .where(ExtractionTemplate.site_id == site_id)
        .order_by(ExtractionRun.id)
    ).all()
    total = 0
    hit = 0
    for run in runs:
        for result in run.field_results or []:
            if result.get("field") == field:
                total += 1
                if result.get("status") == "hit":
                    hit += 1
                break
    if total == 0:
        return 0.5, 0
    return round(hit / total, 4), total


def stability_map(db: Session, site_id: int, field_rules: list[dict]) -> dict[str, float]:
    return {rule["field"]: field_stability(db, site_id, rule["field"])[0] for rule in field_rules}


def history_counts(db: Session, site_id: int, field_rules: list[dict]) -> dict[str, int]:
    return {rule["field"]: field_stability(db, site_id, rule["field"])[1] for rule in field_rules}
