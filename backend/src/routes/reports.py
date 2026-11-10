from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import REPORT_READ_ROLES
from src.controllers import report_controller
from src.middlewares.rbac import Principal, current_principal, require_roles
from src.schemas.report import ReportOut

router = APIRouter(tags=["reports"])


@router.get("/reports/daily", response_model=ReportOut)
def daily_report(
    db: Session = Depends(get_db),
    _=Depends(require_roles(*REPORT_READ_ROLES)),
) -> dict:
    return report_controller.daily_report(db)


@router.get("/reports/daily.csv")
def export_csv(
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(*REPORT_READ_ROLES)),
) -> Response:
    content = report_controller.export_csv(db, principal, request)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pricelens-daily-report.csv"'},
    )


@router.get("/audit-logs")
def audit_logs(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "analyst")),
) -> dict:
    return report_controller.audit_logs(db)
