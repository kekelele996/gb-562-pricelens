from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import RUN_EXECUTE_ROLES
from src.controllers import run_controller
from src.middlewares.rbac import Principal, current_principal, require_roles

READ_ROLES = ("admin", "analyst")
from src.schemas.run import RunCreateIn, RunListOut, RunOut

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=RunListOut)
def list_runs(
    site_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_roles(*READ_ROLES)),
) -> dict:
    return run_controller.list_runs(db, site_id)


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db), _=Depends(require_roles(*READ_ROLES))) -> dict:
    return run_controller.get_run(db, run_id)


@router.post("", response_model=RunOut)
def execute(
    payload: RunCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(*RUN_EXECUTE_ROLES)),
) -> dict:
    return run_controller.execute(db, principal, payload.model_dump(), request)
