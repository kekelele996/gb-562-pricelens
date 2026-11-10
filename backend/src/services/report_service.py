"""客户只读日报：每站点最新成功批次的字段快照 + CSV 导出。"""
from __future__ import annotations

import csv
import io

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.run import ExtractionRun
from src.models.site import Site
from src.models.snapshot import Snapshot
from src.models.template import ExtractionTemplate
from src.utils.timeutil import iso_utc, utcnow

CSV_COLUMNS = [
    "站点", "域名", "快照", "采集时间", "商品标题", "标价", "到手价", "库存状态", "F1", "状态",
]


def _field_value(run: ExtractionRun, field: str) -> str | None:
    for result in run.field_results or []:
        if result.get("field") == field:
            return result.get("value")
    return None


def build_rows(db: Session) -> list[dict]:
    rows: list[dict] = []
    sites = db.scalars(select(Site).order_by(Site.batch_priority, Site.id)).all()
    for site in sites:
        template_ids = db.scalars(
            select(ExtractionTemplate.id).where(ExtractionTemplate.site_id == site.id)
        ).all()
        if not template_ids:
            continue
        run = db.scalars(
            select(ExtractionRun)
            .where(ExtractionRun.template_id.in_(template_ids))
            .order_by(desc(ExtractionRun.id))
            .limit(1)
        ).first()
        if run is None:
            continue
        snapshot = db.get(Snapshot, run.snapshot_id)
        rows.append(
            {
                "site_id": site.id,
                "site_name": site.name,
                "domain": site.domain,
                "snapshot_label": snapshot.label if snapshot else "",
                "captured_at": iso_utc(snapshot.captured_at) if snapshot else "",
                "title": _field_value(run, "title"),
                "list_price": _field_value(run, "list_price"),
                "promo_price": _field_value(run, "promo_price"),
                "stock": _field_value(run, "stock"),
                "f1_score": round(run.f1_score, 4) if run.f1_score is not None else None,
                "status": run.status,
            }
        )
    return rows


def build_report(db: Session) -> dict:
    rows = build_rows(db)
    scored = [row["f1_score"] for row in rows if row["f1_score"] is not None]
    return {
        "generated_at": iso_utc(utcnow()),
        "rows": rows,
        "avg_f1": round(sum(scored) / len(scored), 4) if scored else None,
    }


def export_csv(db: Session) -> str:
    report = build_report(db)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for row in report["rows"]:
        writer.writerow([
            row["site_name"], row["domain"], row["snapshot_label"], row["captured_at"],
            row["title"], row["list_price"], row["promo_price"], row["stock"],
            row["f1_score"], row["status"],
        ])
    return buffer.getvalue()
