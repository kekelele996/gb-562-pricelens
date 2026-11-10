"""客户日报控制器。"""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from src.services import audit_service, report_service


def daily_report(db: Session) -> dict:
    return report_service.build_report(db)


def export_csv(db: Session, principal, request: Request) -> str:
    content = report_service.export_csv(db)
    audit_service.record(
        db,
        actor_email=principal.email,
        actor_role=principal.role,
        action="report.export",
        entity="report",
        entity_id=None,
        detail={"format": "csv", "rows": max(0, content.count("\n") - 1)},
        ip=request.client.host if request.client else None,
    )
    db.commit()
    return content


def audit_logs(db: Session) -> dict:
    return audit_service.list_logs(db)
