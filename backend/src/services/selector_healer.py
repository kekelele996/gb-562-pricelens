"""算法 B：候选选择器自愈评分。

score = 0.4*value_similarity + 0.3*stability + 0.2*specificity + 0.1*(1-hit_penalty)

- value_similarity：候选在新快照抽到的值 vs 模板已验证值（归一化相似度/token Jaccard）
- stability：该站点该字段在历史批次中的正确率（跨模板版本，来自 extraction_runs.field_results）
- specificity：1 - min(1, hit_count / total_nodes)
- hit_penalty：min(1, (hit_count-1)/3)
候选生成顺序固定、无随机；全部候选 miss -> confidence=0, reason=no_candidate。
"""
from __future__ import annotations

import re

from src.services import dom_html
from src.utils.textutil import normalize_value, similarity, value_similarity

KIND_ORDER = {"class_relaxed": 0, "sibling_index": 1, "text_anchor": 2, "fuzzy_text": 3}
AUTO_APPLY_THRESHOLD = 0.78


def _simple_parts(selector: str) -> dict:
    token = selector.strip().split()[-1] if selector.strip() else ""
    tag_match = re.match(r"^([\w*]+)", token)
    tag = tag_match.group(1) if tag_match else "*"
    classes = re.findall(r"\.([\w-]+)", token)
    return {"tag": tag, "classes": classes, "token": token}


def _class_prefixes(classes: list[str]) -> list[str]:
    prefixes: list[str] = []
    for cls in classes:
        head = cls.split("-")[0]
        if len(head) >= 3 and head not in prefixes:
            prefixes.append(head)
    return prefixes


def _new_dom_classes(root) -> list[str]:
    seen: list[str] = []
    for node in dom_html.iter_nodes(root):
        if node.tag in {"#root", "#text"}:
            continue
        for cls in node.classes():
            if cls not in seen:
                seen.append(cls)
    return seen


def generate_selectors(old_selector: str, rule: dict, root) -> list[tuple[str, str]]:
    """生成 (kind, selector) 候选；顺序固定。"""
    parts = _simple_parts(old_selector)
    tag = parts["tag"]
    prefix_list = _class_prefixes(parts["classes"])
    dom_classes = _new_dom_classes(root)
    generated: list[tuple[str, str]] = []

    # ① 旧 selector 的 class 容错变体：同前缀 class 逐个尝试（含父级 token 替换）
    for cls in dom_classes:
        for prefix in prefix_list:
            if cls.startswith(prefix) and cls not in parts["classes"]:
                generated.append(("class_relaxed", f"{tag}.{cls}"))
                break
    tokens_all = [t for t in old_selector.split() if t]
    for index, token in enumerate(tokens_all):
        token_classes = re.findall(r"\.([\w-]+)", token)
        token_prefixes = _class_prefixes(token_classes)
        if not token_prefixes:
            continue
        token_tag_match = re.match(r"^([\w*]+)", token)
        token_tag = token_tag_match.group(1) if token_tag_match else "*"
        for cls in dom_classes:
            for prefix in token_prefixes:
                if cls.startswith(prefix) and cls not in token_classes:
                    replaced = list(tokens_all)
                    replaced[index] = f"{token_tag}.{cls}"
                    generated.append(("class_relaxed", " ".join(replaced)))
                    break

    # ② 同层级兄弟索引：沿用原父级路径 + :nth-of-type(k)
    tokens = [t for t in old_selector.split() if t]
    if len(tokens) >= 2:
        parent = " ".join(tokens[:-1])
        for index in (1, 2, 3):
            generated.append(("sibling_index", f"{parent} {parts['token']}:nth-of-type({index})"))

    # ③ 文本锚点 XPath（用模板字段的中文标签做锚）
    anchor_text = rule.get("anchor_text")
    if anchor_text:
        generated.append(
            (
                "text_anchor",
                f"xpath://*[contains(text(),'{anchor_text}')]/following-sibling::{tag}[1]",
            )
        )

    # ④ tag + 文本模糊匹配（值层兜底）
    generated.append(("fuzzy_text", f"fuzzy::{tag}"))

    deduped: list[tuple[str, str]] = []
    for kind, selector in generated:
        if selector != old_selector and all(sel != selector for _, sel in deduped):
            deduped.append((kind, selector))
    return deduped


def _candidate_values(root, selector: str, rule: dict, expected: str) -> tuple[list[str], float]:
    post_regex = extraction_service_pattern(rule)
    values: list[str] = []
    best_ratio = 0.0
    if selector.startswith("fuzzy::"):
        tag = selector.split("::", 1)[1]
        for node, ratio in dom_html.fuzzy_scan(root, tag, expected)[:200]:
            if ratio < 0.45:
                continue
            raw = node.text()
            if not raw:
                continue
            values.append(raw[:160])
            best_ratio = max(best_ratio, ratio)
            if len(values) >= 25:
                break
        return values, best_ratio
    if selector.startswith("xpath://"):
        nodes = dom_html.text_anchor(root, selector)
    else:
        nodes = dom_html.select(root, selector)
    for node in nodes:
        raw = node.text()
        if not raw:
            continue
        value = _apply_pattern(raw, post_regex)
        if value:
            values.append(value)
    return values, best_ratio


def extraction_service_pattern(rule: dict) -> str | None:
    from src.services.extraction_service import DEFAULT_PATTERNS

    if rule.get("post_regex"):
        return rule["post_regex"]
    return DEFAULT_PATTERNS.get(rule.get("type", ""))


def _apply_pattern(raw: str, pattern: str | None) -> str:
    text = dom_html.normalize(raw)
    if not pattern:
        return normalize_value(text)
    match = re.search(pattern, text)
    if not match:
        return ""
    return match.group(1) if match.groups() else match.group(0)


def score_candidate(
    kind: str,
    selector: str,
    root,
    rule: dict,
    expected: str,
    stability: float,
    total_nodes: int,
) -> dict | None:
    values, fuzzy_ratio = _candidate_values(root, selector, rule, expected)
    if not values:
        return None
    hit_count = len(values)
    primary = values[0]
    vs = max([value_similarity(primary, expected), fuzzy_ratio])
    if kind != "fuzzy_text":
        vs = max(vs, max(value_similarity(v, expected) for v in values))
    vs = round(min(1.0, vs), 4)
    specificity = round(1 - min(1.0, hit_count / max(total_nodes, 1)), 4)
    hit_penalty = round(min(1.0, max(0, hit_count - 1) / 3.0), 4)
    score = round(
        0.4 * vs + 0.3 * stability + 0.2 * specificity + 0.1 * (1 - hit_penalty),
        4,
    )
    return {
        "kind": kind,
        "selector": selector,
        "value": primary,
        "hit_count": hit_count,
        "value_similarity": vs,
        "stability": round(stability, 4),
        "specificity": specificity,
        "hit_penalty": hit_penalty,
        "score": score,
        "auto_applyable": score >= AUTO_APPLY_THRESHOLD and vs >= 0.6,
    }


def heal(
    new_html: str,
    field_rules: list[dict],
    stability_by_field: dict[str, float] | None = None,
    history_counts: dict[str, int] | None = None,
) -> dict:
    """对新快照逐字段生成候选评分；返回 {fields: [...], suggested_patch: {...}}。"""
    from src.services import extraction_service

    stability_by_field = stability_by_field or {}
    history_counts = history_counts or {}
    root = dom_html.parse_html(new_html)
    total_nodes = max(1, dom_html.node_count(root))
    fields: list[dict] = []
    suggested_patch: dict[str, str] = {}

    # 先用旧规则抽取，判断该字段是否需要修复
    current_results, _ = extraction_service.extract_document(new_html, field_rules)
    current_by_field = {r["field"]: r for r in current_results}

    for rule in field_rules:
        field = rule["field"]
        expected = rule.get("verified_value") or ""
        current = current_by_field.get(field, {})
        needs_repair = current.get("status") != "hit"
        stability = stability_by_field.get(field, 0.5)
        candidates: list[dict] = []
        if not needs_repair:
            candidates.append(
                {
                    "kind": "existing",
                    "selector": rule.get("selector_candidates", [""])[0],
                    "value": current.get("value"),
                    "hit_count": 1,
                    "value_similarity": 1.0,
                    "stability": round(stability, 4),
                    "specificity": 0.99,
                    "hit_penalty": 0.0,
                    "score": 1.0,
                    "auto_applyable": False,
                }
            )
        else:
            old_selector = (rule.get("selector_candidates") or [""])[0]
            for kind, selector in generate_selectors(old_selector, rule, root):
                candidate = score_candidate(kind, selector, root, rule, expected, stability, total_nodes)
                if candidate is not None:
                    candidates.append(candidate)
            candidates.sort(key=lambda c: (-c["score"], KIND_ORDER.get(c["kind"], 9), c["selector"]))
            candidates = candidates[:3]

        top = candidates[0] if candidates else None
        entry = {
            "field": field,
            "label": rule.get("label", field),
            "needs_repair": needs_repair,
            "current_status": current.get("status", "miss"),
            "current_value": current.get("value"),
            "verified_value": expected,
            "stability": round(stability, 4),
            "history_runs": history_counts.get(field, 0),
            "candidates": candidates,
            "selected": top["selector"] if top and top.get("auto_applyable") else None,
            "confidence": round(top["score"], 4) if top else 0.0,
            "reason": None
            if top and top.get("auto_applyable")
            else ("not_needed" if not needs_repair else ("no_candidate" if not candidates else "low_confidence")),
        }
        fields.append(entry)
        if entry["selected"]:
            suggested_patch[field] = entry["selected"]

    return {
        "status": "ok",
        "fields": fields,
        "suggested_patch": suggested_patch,
        "auto_apply_count": len(suggested_patch),
        "threshold": AUTO_APPLY_THRESHOLD,
    }


def apply_patch(field_rules: list[dict], patch: dict[str, str], note: str | None = None) -> list[dict]:
    """把 patch 里的 selector 提升为对应字段的首选候选，返回新的 field_rules 深拷贝。"""
    import copy

    updated = copy.deepcopy(field_rules)
    for rule in updated:
        selector = patch.get(rule["field"])
        if not selector:
            continue
        candidates = [c for c in rule.get("selector_candidates", []) if c != selector]
        rule["selector_candidates"] = [selector] + candidates
        rule["patched"] = True
        if note:
            rule["patch_note"] = note
    return updated
