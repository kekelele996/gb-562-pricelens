"""幂等 seed：3 账号 / 6 站点 / 8 模板（47 条字段规则）/ 12 快照 / 12 批次 / 4 告警。

自然键 upsert：users.email、sites.domain、templates(site,name,version)、
snapshots(site,dom_hash)、runs.seed_key、alerts(site,snapshot)。重复执行不新增、不覆盖用户修改。
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from sqlalchemy import func, select

from src.config.database import session_scope
from src.config.settings import settings
from src.constants.enums import AlertStatus, SiteStatus, TemplateStatus
from src.models.alert import DriftAlert
from src.models.audit import AuditLog
from src.models.run import ExtractionRun
from src.models.site import Site
from src.models.snapshot import Snapshot
from src.models.template import ExtractionTemplate
from src.models.user import User
from scripts.build_snapshots import SITES, SiteSpec, build_snapshot_html, snapshot_url
from scripts.demo_config import DRAFT_RULES, field_rules_for
from src.services import run_service, snapshot_service
from src.utils.security import hash_password

DEMO_PASSWORD = "Demo@2026"
DEMO_USERS = [
    ("admin@pricelens.io", "运营主管 · 周敏", "admin"),
    ("analyst@pricelens.io", "采集工程师 · 陈拓", "analyst"),
    ("client@pricelens.io", "品牌客户 · 林岚（只读）", "client"),
]
BASE_TIME = datetime(2026, 11, 3, 6, 0, 0)
NEW_TIME = datetime(2026, 11, 10, 6, 0, 0)


def dom_hash(html: str) -> str:
    return hashlib.sha256(html.encode("utf-8")).hexdigest()


def ensure_users(db) -> dict[str, User]:
    users: dict[str, User] = {}
    for email, display_name, role in DEMO_USERS:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is None:
            existing = User(
                email=email,
                password_hash=hash_password(DEMO_PASSWORD),
                display_name=display_name,
                role=role,
            )
            db.add(existing)
            db.flush()
        users[email] = existing
    return users


def ensure_site(db, spec: SiteSpec) -> Site:
    site = db.scalar(select(Site).where(Site.domain == spec.domain))
    if site is None:
        site = Site(
            name=spec.name,
            domain=spec.domain,
            market=spec.market,
            robots_policy=spec.robots_policy,
            qps_limit=spec.qps_limit,
            status=spec.status,
            batch_priority=spec.priority,
            note=f"{spec.market}市场 · 3C/家电价格监测",
        )
        db.add(site)
        db.flush()
    return site


def ensure_snapshot(db, site: Site, spec: SiteSpec, variant: str) -> Snapshot:
    html = build_snapshot_html(spec, variant)
    digest = dom_hash(html)
    snapshot = db.scalar(select(Snapshot).where(Snapshot.site_id == site.id, Snapshot.dom_hash == digest))
    if snapshot is None:
        captured = BASE_TIME if variant == "baseline" else NEW_TIME + timedelta(minutes=spec.priority)
        if spec.drift_level == "none" and variant == "new":
            captured = NEW_TIME + timedelta(days=1)
        snapshot = Snapshot(
            site_id=site.id,
            url=snapshot_url(spec),
            label="baseline 2026-11-03 06:00" if variant == "baseline" else captured.strftime("daily %Y-%m-%d %H:%M"),
            captured_at=captured,
            html=html,
            dom_hash=digest,
            byte_size=len(html.encode("utf-8")),
            is_baseline=(variant == "baseline"),
        )
        db.add(snapshot)
        db.flush()
    return snapshot


def ensure_template(db, site: Site, name: str, version: int, rules: list[dict],
                    status: str, coverage: float, note: str, verified: datetime | None) -> ExtractionTemplate:
    template = db.scalar(
        select(ExtractionTemplate).where(
            ExtractionTemplate.site_id == site.id,
            ExtractionTemplate.name == name,
            ExtractionTemplate.version == version,
        )
    )
    if template is None:
        template = ExtractionTemplate(
            site_id=site.id,
            name=name,
            version=version,
            status=status,
            field_rules=rules,
            coverage_score=coverage,
            last_verified_at=verified,
            change_note=note,
        )
        db.add(template)
        db.flush()
    return template


def ensure_run(db, template: ExtractionTemplate, snapshot: Snapshot, seed_key: str,
               triggered_by: str, force_failed_reason: str | None = None) -> ExtractionRun:
    run = db.scalar(select(ExtractionRun).where(ExtractionRun.seed_key == seed_key))
    if run is not None:
        return run
    return run_service.execute_run(
        db, template, snapshot, triggered_by=triggered_by, seed_key=seed_key,
        force_failed_reason=force_failed_reason,
    )


def ensure_alert(db, snapshot: Snapshot, template: ExtractionTemplate) -> DriftAlert | None:
    existing = db.scalar(
        select(DriftAlert).where(
            DriftAlert.site_id == snapshot.site_id,
            DriftAlert.snapshot_id == snapshot.id,
        )
    )
    if existing is not None:
        return existing
    return snapshot_service.upsert_alert(db, snapshot, template)


def ensure_seed_audit(db, users: dict[str, User]) -> None:
    entries = [
        ("seed:audit:1", "admin@pricelens.io", "admin", "auth.login", "user", "1", {"role": "admin"}),
        ("seed:audit:2", "analyst@pricelens.io", "analyst", "template.update", "template", "1",
         {"field_count": 7, "version": 1}),
    ]
    for seed_key, email, role, action, entity, entity_id, detail in entries:
        exists = db.scalar(select(AuditLog).where(AuditLog.seed_key == seed_key))
        if exists is None:
            db.add(AuditLog(
                actor_email=email, actor_role=role, action=action, entity=entity,
                entity_id=entity_id, detail=detail, layer="seed", ip="127.0.0.1",
                seed_key=seed_key,
            ))
    db.flush()


def seed_all() -> str:
    """执行一次幂等 seed，返回 SEED_SUMMARY 行。"""
    with session_scope() as db:
        users = ensure_users(db)
        specs_by_key = {spec.key: spec for spec in SITES}
        sites: dict[str, Site] = {}
        templates: dict[str, ExtractionTemplate] = {}
        snapshots: dict[str, dict[str, Snapshot]] = {}

        for spec in SITES:
            site = ensure_site(db, spec)
            sites[spec.key] = site
            snapshots[spec.key] = {
                "baseline": ensure_snapshot(db, site, spec, "baseline"),
                "new": ensure_snapshot(db, site, spec, "new"),
            }

        # 京选超市：PC 商品页 v1（生效中）+ 移动版 H5 旧模板（已归档），演示版本管理
        jing = specs_by_key["jingxuan"]
        v0_rules = field_rules_for(jing, with_coupon=True)
        for rule in v0_rules:
            if rule["field"] == "coupon_price":
                rule["selector_candidates"] = ["div.coupon-site span.coupon-amount"]
        templates["jingxuan:mobile"] = ensure_template(
            db, sites["jingxuan"], "京选超市 · 移动版 H5", 1, v0_rules,
            TemplateStatus.DEPRECATED.value, 0.68, "移动版旧模板（2026-06），已并入 PC 模板",
            datetime(2026, 6, 18, 10, 20),
        )
        v1_rules = field_rules_for(jing, with_coupon=True)
        templates["jingxuan:v1"] = ensure_template(
            db, sites["jingxuan"], "京选超市 · PC 商品页", 1, v1_rules,
            TemplateStatus.ACTIVE.value, 0.9, "PC 商品页首版：7 字段 / 47 条规则之一",
            datetime(2026, 10, 28, 15, 5),
        )
        for spec in SITES[1:]:
            rules = field_rules_for(spec, with_coupon=False)
            templates[f"{spec.key}:v1"] = ensure_template(
                db, sites[spec.key], f"{spec.name} · 商品详情", 1, rules,
                TemplateStatus.ACTIVE.value, 0.82,
                f"{spec.market}站点首版模板", datetime(2026, 9, 12, 9, 30),
            )
        templates["doudian:draft"] = ensure_template(
            db, sites["doudian"], "抖店商城 · 移动版草稿", 1, DRAFT_RULES,
            TemplateStatus.DRAFT.value, 0.35, "移动版草稿：字段未验证，覆盖率低",
            None,
        )

        # 12 条真实批次：先 v0，再 v1 baseline，再漂移快照
        ensure_run(db, templates["jingxuan:mobile"], snapshots["jingxuan"]["baseline"],
                   "seed:run:jingxuan:mobile:baseline", "analyst@pricelens.io")
        ensure_run(db, templates["jingxuan:v1"], snapshots["jingxuan"]["baseline"],
                   "seed:run:jingxuan:v1:baseline", "analyst@pricelens.io")
        ensure_run(db, templates["jingxuan:v1"], snapshots["jingxuan"]["new"],
                   "seed:run:jingxuan:v1:drifted", "schedule:06:00")
        for key in ("taohuasuan", "pinyigou"):
            ensure_run(db, templates[f"{key}:v1"], snapshots[key]["baseline"],
                       f"seed:run:{key}:baseline", "analyst@pricelens.io")
            ensure_run(db, templates[f"{key}:v1"], snapshots[key]["new"],
                       f"seed:run:{key}:drifted", "schedule:06:00")
        ensure_run(db, templates["suningkuaigou:v1"], snapshots["suningkuaigou"]["baseline"],
                   "seed:run:suningkuaigou:baseline", "analyst@pricelens.io")
        ensure_run(db, templates["suningkuaigou:v1"], snapshots["suningkuaigou"]["new"],
                   "seed:run:suningkuaigou:drifted", "schedule:06:00",
                   force_failed_reason="抓取超时（模拟 30s HTTP timeout），未写入字段结果")
        ensure_run(db, templates["doudian:v1"], snapshots["doudian"]["baseline"],
                   "seed:run:doudian:baseline", "analyst@pricelens.io")
        ensure_run(db, templates["doudian:v1"], snapshots["doudian"]["new"],
                   "seed:run:doudian:drifted", "schedule:06:00")
        ensure_run(db, templates["xhsgoods:v1"], snapshots["xhsgoods"]["baseline"],
                   "seed:run:xhsgoods:baseline", "analyst@pricelens.io")

        # 4 条告警：抖动阈值触发（high2 / medium1 / low1），诊断与候选均为真算
        for key in ("jingxuan", "taohuasuan", "pinyigou", "suningkuaigou"):
            ensure_alert(db, snapshots[key]["new"], templates[f"{key}:v1"])

        for key, site in sites.items():
            latest = snapshots[key]["new"]
            site.last_crawled_at = latest.captured_at

        ensure_seed_audit(db, users)

        summary = (
            f"SEED_SUMMARY brand=pricelens "
            f"sites={db.scalar(select(func.count()).select_from(Site))} "
            f"templates={db.scalar(select(func.count()).select_from(ExtractionTemplate))} "
            f"snapshots={db.scalar(select(func.count()).select_from(Snapshot))} "
            f"runs={db.scalar(select(func.count()).select_from(ExtractionRun))} "
            f"alerts={db.scalar(select(func.count()).select_from(DriftAlert))} "
            f"users={db.scalar(select(func.count()).select_from(User))}"
        )
        field_rules = sum(
            len(t.field_rules or []) for t in db.scalars(select(ExtractionTemplate)).all()
        )
        detail = f"SEED_DETAIL brand=pricelens field_rules={field_rules} mode=idempotent"
    print(summary)
    print(detail)
    return summary


if __name__ == "__main__":
    seed_all()
