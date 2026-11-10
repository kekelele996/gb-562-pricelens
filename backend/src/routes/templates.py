from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import TEMPLATE_WRITE_ROLES

READ_ROLES = ("admin", "analyst")
from src.controllers import template_controller
from src.middlewares.rbac import Principal, current_principal, require_roles
from src.schemas.template import PreviewOut, TemplateOut, TemplatePatchIn

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db), _=Depends(require_roles(*READ_ROLES))) -> dict:
    return template_controller.get_template(db, template_id)


@router.patch("/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: int,
    payload: TemplatePatchIn,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(*TEMPLATE_WRITE_ROLES)),
) -> dict:
    return template_controller.update_template(db, template_id, principal, payload.model_dump(), request)


@router.get("/{template_id}/preview", response_model=PreviewOut)
def preview(
    template_id: int,
    snapshot_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_roles(*READ_ROLES)),
) -> dict:
    return template_controller.preview(db, template_id, snapshot_id)
