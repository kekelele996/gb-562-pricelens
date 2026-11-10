"""站点与模板总览。"""
from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from src.constants.enums import AlertStatus, SiteStatus, TemplateStatus
from src.models.alert import DriftAlert
from src.models.site import Site
from src.models.template import ExtractionTemplate
from src.utils.timeutil import iso_utc


def _template_brief(template: ExtractionTemplate) -> dict:
    return {
        "id": template.id,
        "name": template.name,
        "version": template.version,
        "status": template.status,
        "coverage_score": round(template.coverage_score, 4),
        "field_count": len(template.field_rules or []),
    }


def list_sites(db: Session) -> dict:
    sites = db.scalars(select(Site).order_by(Site.batch_priority, Site.id)).all()
    items = []
    for site in sites:
        templates = db.scalars(
            select(ExtractionTemplate)
            .where(ExtractionTemplate.site_id == site.id)
            .order_by(desc(ExtractionTemplate.version))
        ).all()
        alert_count = db.scalar(
            select(func.count()).select_from(DriftAlert).where(
                DriftAlert.site_id == site.id,
                DriftAlert.status == AlertStatus.OPEN.value,
            )
        ) or 0
        items.append(
            {
                "id": site.id,
                "name": site.name,
                "domain": site.domain,
                "market": site.market,
                "robots_policy": site.robots_policy,
                "qps_limit": site.qps_limit,
                "status": site.status,
                "note": site.note,
                "alert_count": alert_count,
                "last_crawled_at": iso_utc(site.last_crawled_at),
                "templates": [_template_brief(t) for t in templates if t.status != TemplateStatus.DRAFT.value or True],
            }
        )
    return {"items": items, "total": len(items)}


def get_site(db: Session, site_id: int) -> Site | None:
    return db.get(Site, site_id)


def create_site(db: Session, payload: dict) -> Site:
    site = Site(
        name=payload["name"],
        domain=payload["domain"].lower().strip(),
        market=payload.get("market", "全国"),
        robots_policy=payload.get("robots_policy", "partial"),
        qps_limit=payload.get("qps_limit", 1.0),
        status=payload.get("status", SiteStatus.ACTIVE.value),
        note=payload.get("note"),
        batch_priority=9,
    )
    db.add(site)
    db.flush()
    return site


def overview(db: Session) -> dict:
    site_total = db.scalar(select(func.count()).select_from(Site)) or 0
    active_sites = db.scalar(select(func.count()).select_from(Site).where(Site.status == SiteStatus.ACTIVE.value)) or 0
    template_total = db.scalar(select(func.count()).select_from(ExtractionTemplate)) or 0
    active_templates = db.scalar(
        select(func.count()).select_from(ExtractionTemplate).where(ExtractionTemplate.status == TemplateStatus.ACTIVE.value)
    ) or 0
    open_alerts = db.scalar(
        select(func.count()).select_from(DriftAlert).where(DriftAlert.status == AlertStatus.OPEN.value)
    ) or 0
    severity_rows = db.execute(
        select(DriftAlert.severity, func.count()).where(DriftAlert.status == AlertStatus.OPEN.value).group_by(DriftAlert.severity)
    ).all()
    severity_counts = {row[0]: row[1] for row in severity_rows}
    return {
        "sites": site_total,
        "active_sites": active_sites,
        "templates": template_total,
        "active_templates": active_templates,
        "open_alerts": open_alerts,
        "severity_counts": severity_counts,
    }
