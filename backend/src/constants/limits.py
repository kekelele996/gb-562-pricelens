"""限流与跑批约束常量。"""
from __future__ import annotations

RATE_WINDOW_SECONDS = 60
RUN_BUCKET_KEY = "runs"
F1_CORRECT_THRESHOLD = 0.82   # 字段值与已验证值归一化相似度 >= 0.88 记为正确
MAX_PREVIEW_SNIPPET = 220
MAX_TOP_CHANGED_SUBTREES = 3
DRIFT_HIGH = 0.35
DRIFT_MEDIUM = 0.18
