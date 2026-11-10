"""ORM 模型聚合导出（Base 用于 create_all）。"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from src.models.user import User  # noqa: E402
from src.models.site import Site  # noqa: E402
from src.models.template import ExtractionTemplate  # noqa: E402
from src.models.snapshot import Snapshot  # noqa: E402
from src.models.run import ExtractionRun  # noqa: E402
from src.models.alert import DriftAlert  # noqa: E402
from src.models.audit import AuditLog  # noqa: E402

__all__ = [
    "Base", "User", "Site", "ExtractionTemplate", "Snapshot",
    "ExtractionRun", "DriftAlert", "AuditLog",
]
