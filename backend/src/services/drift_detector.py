"""算法 A：DOM 结构漂移诊断（标准库实现，无随机，可复现）。

drift = 0.4*(1-path_jaccard) + 0.2*node_ratio_delta + 0.2*(1-text_sim) + 0.2*field_miss_delta
阈值：>=0.35 high / 0.18~0.35 medium / <0.18 low（<0.10 不生成告警）
"""
from __future__ import annotations

from difflib import SequenceMatcher

from src.constants.enums import Severity
from src.constants.limits import DRIFT_HIGH, DRIFT_MEDIUM, MAX_TOP_CHANGED_SUBTREES
from src.services import dom_html, extraction_service


def jaccard(a: dict[str, int], b: dict[str, int]) -> float:
    keys_a, keys_b = set(a), set(b)
    if not keys_a and not keys_b:
        return 1.0
    return len(keys_a & keys_b) / len(keys_a | keys_b)


def severity_of(score: float) -> str:
    if score >= DRIFT_HIGH:
        return Severity.HIGH.value
    if score >= DRIFT_MEDIUM:
        return Severity.MEDIUM.value
    if score >= 0.09:
        return Severity.LOW.value
    return Severity.NONE.value


def field_hit_rate(results: list[dict]) -> float:
    if not results:
        return 0.0
    return sum(1 for r in results if r["value"]) / len(results)


def diagnose(baseline_html: str, new_html: str, field_rules: list[dict]) -> dict:
    """输入 baseline/新快照 HTML + 模板字段规则，输出落库到 DriftAlert.diagnosis 的结构。"""
    try:
        baseline_root = dom_html.parse_html(baseline_html)
        new_root = dom_html.parse_html(new_html)
        if not baseline_root.children or not new_root.children:
            raise ValueError("empty_dom")

        baseline_paths = dom_html.path_multiset(baseline_root)
        new_paths = dom_html.path_multiset(new_root)
        path_jaccard = round(jaccard(baseline_paths, new_paths), 4)

        base_nodes = dom_html.node_count(baseline_root)
        new_nodes = dom_html.node_count(new_root)
        node_ratio_delta = round(min(1.0, abs(new_nodes - base_nodes) / max(base_nodes, 1)), 4)

        baseline_text = dom_html.all_text(baseline_root)[:20000]
        new_text = dom_html.all_text(new_root)[:20000]
        text_sim = round(SequenceMatcher(None, baseline_text, new_text).ratio(), 4)

        baseline_results, _ = extraction_service.extract_document(baseline_html, field_rules)
        new_results, _ = extraction_service.extract_document(new_html, field_rules)
        base_hit = field_hit_rate(baseline_results)
        new_hit = field_hit_rate(new_results)
        field_miss_delta = round(max(0.0, base_hit - new_hit), 4)

        drift = round(
            0.4 * (1 - path_jaccard)
            + 0.2 * node_ratio_delta
            + 0.2 * (1 - text_sim)
            + 0.2 * field_miss_delta,
            4,
        )
        changed = dom_html.group_changed_subtrees(baseline_paths, new_paths)[:MAX_TOP_CHANGED_SUBTREES]

        reason_codes: list[str] = []
        if path_jaccard < 0.75:
            reason_codes.append(f"path_jaccard={path_jaccard:.3f}（结构路径重合度低）")
        if node_ratio_delta >= 0.15:
            reason_codes.append(f"node_ratio_delta={node_ratio_delta:.3f}（节点数变化 {base_nodes}→{new_nodes}）")
        if text_sim < 0.75:
            reason_codes.append(f"text_similarity={text_sim:.3f}（正文本相似度低）")
        miss_fields = [r["field"] for r in new_results if r["status"] != "hit"]
        if field_miss_delta > 0:
            reason_codes.append(f"field_miss_delta={field_miss_delta:.3f}（字段命中率 {base_hit:.2f}→{new_hit:.2f}）")
        for changed_subtree in changed:
            reason_codes.append(
                f"changed_subtree={changed_subtree['path']} (+{changed_subtree['added']}/-{changed_subtree['removed']})"
            )

        matrix = [
            {
                "field": r["field"],
                "label": r["label"],
                "baseline_value": base["value"],
                "baseline_status": base["status"],
                "new_value": r["value"],
                "new_status": r["status"],
                "similarity": r["similarity"],
                "matched_selector": r["matched_selector"],
            }
            for r, base in zip(new_results, baseline_results)
        ]

        return {
            "status": "ok",
            "drift_score": drift,
            "severity": severity_of(drift),
            "components": {
                "path_jaccard": path_jaccard,
                "node_ratio_delta": node_ratio_delta,
                "text_similarity": text_sim,
                "field_miss_delta": field_miss_delta,
                "baseline_node_count": base_nodes,
                "new_node_count": new_nodes,
            },
            "top_changed_subtrees": changed,
            "reason_codes": reason_codes,
            "field_matrix": matrix,
            "affected_fields": miss_fields,
        }
    except Exception as exc:  # noqa: BLE001 - 解析失败要落库为 unknown，不能吞掉原因
        return {
            "status": "unknown",
            "drift_score": 0.0,
            "severity": Severity.NONE.value,
            "reason": f"html_parse_failed: {exc}",
            "components": {},
            "top_changed_subtrees": [],
            "reason_codes": ["diagnosis_unknown"],
            "field_matrix": [],
            "affected_fields": [],
        }
