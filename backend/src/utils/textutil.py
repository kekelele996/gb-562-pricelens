"""文本归一化 / 相似度 / 数值描述（算法与报表共用）。"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

_SPACE_RE = re.compile(r"\s+")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return _SPACE_RE.sub(" ", value.replace("\u3000", " ")).strip()


def normalize_value(value: str | None) -> str:
    """归一化字段值：全角符号/货币符号/千分位/空白。"""
    text = normalize_text(value)
    text = text.replace("￥", "¥").replace("，", ",").replace("：", ":")
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)
    text = re.sub(r"\s*¥\s*", "¥", text)
    return text.strip()


def extract_number(value: str | None) -> float | None:
    text = normalize_value(value).replace(",", "")
    match = _NUM_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def similarity(a: str | None, b: str | None) -> float:
    """SequenceMatcher 口径；数值型字段优先用数值相对误差。"""
    na, nb = normalize_value(a), normalize_value(b)
    if not na or not nb:
        return 0.0
    number_a, number_b = extract_number(na), extract_number(nb)
    if number_a is not None and number_b is not None and not re.search(r"[^\d,.\-¥%条]", na + nb):
        base = max(abs(number_a), abs(number_b), 1.0)
        numeric_sim = max(0.0, 1.0 - abs(number_a - number_b) / base)
        return round(max(numeric_sim, SequenceMatcher(None, na, nb).ratio()), 4)
    return round(SequenceMatcher(None, na, nb).ratio(), 4)


def token_jaccard(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", (a or "").lower()))
    tb = set(re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", (b or "").lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def value_similarity(a: str | None, b: str | None) -> float:
    """算法 B 的 value_similarity：max(归一化相似度, token Jaccard)。"""
    return round(max(similarity(a, b), token_jaccard(normalize_value(a), normalize_value(b))), 4)


def short_snippet(html_text: str, limit: int = 220) -> str:
    text = normalize_text(re.sub(r"<[^>]+>", " ", html_text))
    return text[:limit]
