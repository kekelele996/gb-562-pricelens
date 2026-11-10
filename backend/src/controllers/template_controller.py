"""模板控制器。"""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from src.services import audit_service, template_service
from src.utils.errors import AppError


def get_template(db: Session, template_id: int) -> dict:
    template = template_service.get_template(db, template_id)
    if template is None:
        raise AppError("NOT_FOUND", 404)
    data = template_service.serialize_template(db, template)
    data["runs"] = []
    return data


def update_template(db: Session, template_id: int, principal, payload: dict, request: Request) -> dict:
    template = template_service.get_template(db, template_id)
    if template is None:
        raise AppError("NOT_FOUND", 404)
    rules = [rule.model_dump() if hasattr(rule, "model_dump") else dict(rule) for rule in payload["field_rules"]]
    template_service.update_rules(db, template, rules, payload.get("change_note"))
    audit_service.record(
        db,
        actor_email=principal.email,
        actor_role=principal.role,
        action="template.update",
        entity="template",
        entity_id=template.id,
        detail={"field_count": len(rules), "version": template.version},
        ip=request.client.host if request.client else None,
    )
    db.commit()
    return template_service.serialize_template(db, template)


def preview(db: Session, template_id: int, snapshot_id: int | None) -> dict:
    template = template_service.get_template(db, template_id)
    if template is None:
        raise AppError("NOT_FOUND", 404)
    try:
        return template_service.preview(db, template, snapshot_id)
    except ValueError as exc:
        raise AppError("NOT_FOUND", 404, detail=str(exc)) from exc
