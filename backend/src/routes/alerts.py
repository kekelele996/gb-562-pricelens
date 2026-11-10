from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import ALERT_HANDLE_ROLES, RUN_EXECUTE_ROLES
from src.controllers import alert_controller
from src.middlewares.rbac import Principal, current_principal, require_roles

READ_ROLES = ("admin", "analyst")
from src.schemas.snapshot import AlertListOut, AlertOut, AlertStatusIn, AlertStatusOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListOut)
def list_alerts(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_roles(*READ_ROLES)),
) -> dict:
    return alert_controller.list_alerts(db, status)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db), _=Depends(require_roles(*READ_ROLES))) -> dict:
    return alert_controller.get_alert(db, alert_id)


@router.post("/{alert_id}/candidates")
def recompute_candidates(
    alert_id: int,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(*RUN_EXECUTE_ROLES)),
) -> dict:
    return alert_controller.recompute_candidates(db, alert_id, principal, request)


@router.post("/{alert_id}/status", response_model=AlertStatusOut)
def change_status(
    alert_id: int,
    payload: AlertStatusIn,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(*ALERT_HANDLE_ROLES)),
) -> dict:
    return alert_controller.change_status(db, alert_id, principal, payload.model_dump(), request)


@router.post("/{alert_id}/apply")
def apply_patch(
    alert_id: int,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(*RUN_EXECUTE_ROLES)),
) -> dict:
    return alert_controller.apply_patch(db, alert_id, principal, request)
