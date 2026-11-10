"""站点控制器。"""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from src.services import audit_service, site_service
from src.utils.errors import AppError


def list_sites(db: Session) -> dict:
    return site_service.list_sites(db)


def overview(db: Session) -> dict:
    return site_service.overview(db)


def get_site(db: Session, site_id: int) -> dict:
    site = site_service.get_site(db, site_id)
    if site is None:
        raise AppError("NOT_FOUND", 404)
    data = site_service.list_sites(db)
    for item in data["items"]:
        if item["id"] == site_id:
            return item
    raise AppError("NOT_FOUND", 404)


def create_site(db: Session, principal, payload: dict, request: Request) -> dict:
    existing = site_service.list_sites(db)
    if any(item["domain"] == payload["domain"].lower().strip() for item in existing["items"]):
        raise AppError("CONFLICT", 409, detail="domain_exists")
    site = site_service.create_site(db, payload)
    audit_service.record(
        db,
        actor_email=principal.email,
        actor_role=principal.role,
        action="site.create",
        entity="site",
        entity_id=site.id,
        detail={"name": site.name, "domain": site.domain},
        ip=request.client.host if request.client else None,
    )
    db.commit()
    return {"id": site.id, "name": site.name, "domain": site.domain}
