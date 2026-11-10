from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import RUN_EXECUTE_ROLES
from src.controllers import snapshot_controller
from src.middlewares.rbac import Principal, current_principal, require_roles

READ_ROLES = ("admin", "analyst")
from src.schemas.snapshot import AlertOut, DiagnoseIn

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("")
def list_snapshots(
    site_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_roles(*READ_ROLES)),
) -> dict:
    return snapshot_controller.list_snapshots(db, site_id)


@router.get("/{snapshot_id}")
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db), _=Depends(require_roles(*READ_ROLES))) -> dict:
    return snapshot_controller.get_snapshot(db, snapshot_id)


@router.post("/{snapshot_id}/diagnose", response_model=AlertOut)
def diagnose(
    snapshot_id: int,
    payload: DiagnoseIn,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(*RUN_EXECUTE_ROLES)),
) -> dict:
    return snapshot_controller.diagnose(db, snapshot_id, payload.template_id, principal, request)
