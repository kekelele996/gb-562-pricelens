"""字段抽取：模板 field_rules -> 逐字段结果（含 hit / wrong / miss 判定）。"""
from __future__ import annotations

import re

from src.constants.limits import F1_CORRECT_THRESHOLD
from src.services import dom_html
from src.utils.textutil import short_snippet, similarity

DEFAULT_PATTERNS = {
    "price": r"[0-9][0-9,]*(?:\.[0-9]+)?",
    "count": r"[0-9][0-9,]*",
}


class SnapshotTooLarge(ValueError):
    pass


def apply_post_regex(raw: str, post_regex: str | None) -> str:
    text = dom_html.normalize(raw)
    if not post_regex:
        return text
    match = re.search(post_regex, text)
    if not match:
        return ""
    return match.group(1) if match.groups() else match.group(0)


def rule_pattern(rule: dict) -> str | None:
    if rule.get("post_regex"):
        return rule["post_regex"]
    return DEFAULT_PATTERNS.get(rule.get("type", ""))


def _select_nodes(root, selector: str, expected: str | None) -> list:
    if selector.startswith("fuzzy::"):
        tag = selector.split("::", 1)[1]
        return [node for node, ratio in dom_html.fuzzy_scan(root, tag, expected or "")[:1]]
    if selector.startswith("xpath://"):
        return dom_html.text_anchor(root, selector)
    return dom_html.select(root, selector)


def _snippet_for(node) -> str:
    parent_text = node.parent.text() if node.parent is not None else node.text()
    return short_snippet(parent_text or node.text(), 180)


def extract_field(root, rule: dict) -> dict:
    expected = rule.get("verified_value")
    post_regex = rule_pattern(rule)
    for selector in rule.get("selector_candidates") or []:
        nodes = _select_nodes(root, selector, expected)
        if not nodes:
            continue
        for node in nodes:
            value = apply_post_regex(node.text(), post_regex)
            if not value:
                continue
            status = "hit"
            sim = similarity(value, expected) if expected else 1.0
            if expected and sim < F1_CORRECT_THRESHOLD:
                status = "wrong"
            return {
                "field": rule["field"],
                "label": rule.get("label", rule["field"]),
                "type": rule.get("type", "text"),
                "value": value,
                "raw": node.text()[:160],
                "status": status,
                "similarity": round(sim, 4),
                "matched_selector": selector,
                "snippet": _snippet_for(node),
            }
    return {
        "field": rule["field"],
        "label": rule.get("label", rule["field"]),
        "type": rule.get("type", "text"),
        "value": None,
        "raw": None,
        "status": "miss",
        "similarity": 0.0,
        "matched_selector": None,
        "snippet": None,
    }


def extract_document(html: str, field_rules: list[dict]) -> tuple[list[dict], dict]:
    root = dom_html.parse_html(html)
    results = [extract_field(root, rule) for rule in field_rules]
    stats = {
        "node_count": dom_html.node_count(root),
        "text_length": len(dom_html.all_text(root)),
        "extracted": sum(1 for r in results if r["value"]),
        "correct": sum(1 for r in results if r["status"] == "hit"),
        "wrong": sum(1 for r in results if r["status"] == "wrong"),
        "miss": sum(1 for r in results if r["status"] == "miss"),
    }
    return results, stats


def score_f1(results: list[dict], expected_fields: int) -> tuple[float, dict]:
    """F1 = 2*TP / (2*TP + FP + FN)；TP=hit，FP=wrong，FN=miss(含未抽到)。"""
    tp = sum(1 for r in results if r["status"] == "hit")
    fp = sum(1 for r in results if r["status"] == "wrong")
    fn = max(0, expected_fields - tp)
    denominator = 2 * tp + fp + fn
    f1 = 0.0 if denominator == 0 else round(2 * tp / denominator, 4)
    precision = 0.0 if tp + fp == 0 else round(tp / (tp + fp), 4)
    recall = 0.0 if expected_fields == 0 else round(tp / expected_fields, 4)
    return f1, {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall}
