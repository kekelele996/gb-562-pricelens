from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import SITE_WRITE_ROLES
from src.controllers import site_controller
from src.middlewares.rbac import Principal, current_principal, require_roles
from src.schemas.site import SiteCreateIn, SiteListOut

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=SiteListOut)
def list_sites(db: Session = Depends(get_db), _=Depends(current_principal)) -> dict:
    return site_controller.list_sites(db)


@router.get("/overview")
def overview(db: Session = Depends(get_db), _=Depends(current_principal)) -> dict:
    return site_controller.overview(db)


@router.get("/{site_id}")
def get_site(site_id: int, db: Session = Depends(get_db), _=Depends(current_principal)) -> dict:
    return site_controller.get_site(db, site_id)


@router.post("")
def create_site(
    payload: SiteCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(*SITE_WRITE_ROLES)),
) -> dict:
    return site_controller.create_site(db, principal, payload.model_dump(), request)
