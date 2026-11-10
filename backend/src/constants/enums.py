"""后端共享枚举（前端 frontend/src/constants/enums.ts 与之对应）。"""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"          # 运营主管
    ANALYST = "analyst"      # 采集工程师
    CLIENT = "client"        # 品牌客户（只读）


class RobotsPolicy(str, Enum):
    ALLOW = "allow"
    PARTIAL = "partial"
    BLOCKED = "blocked"


class SiteStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"


class TemplateStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class FieldStatus(str, Enum):
    HIT = "hit"        # 抽到且与已验证值一致
    WRONG = "wrong"    # 抽到但与已验证值不一致（静默错位）
    MISS = "miss"      # 未抽到


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"


class FieldType(str, Enum):
    TEXT = "text"
    PRICE = "price"
    COUNT = "count"
    STOCK = "stock"


class CandidateKind(str, Enum):
    CLASS_RELAXED = "class_relaxed"
    SIBLING_INDEX = "sibling_index"
    TEXT_ANCHOR = "text_anchor"
    FUZZY_TEXT = "fuzzy_text"
