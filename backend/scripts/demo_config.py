"""seed 演示配置：站点字段规则（模板 field_rules 的唯一定义处）。"""
from __future__ import annotations

from scripts.build_snapshots import SITES, SiteSpec

PRICE_REGEX = r"[0-9][0-9,]*(?:\.[0-9]+)?"
COUNT_REGEX = r"[0-9][0-9,]*"


def _rule(field: str, label: str, field_type: str, selector: str, verified: str,
          anchor: str | None = None, post_regex: str | None = None) -> dict:
    return {
        "field": field,
        "label": label,
        "type": field_type,
        "selector_candidates": [selector],
        "post_regex": post_regex if post_regex is not None else (
            PRICE_REGEX if field_type == "price" else (COUNT_REGEX if field_type == "count" else None)
        ),
        "verified_value": verified,
        "anchor_text": anchor,
    }


def field_rules_for(site: SiteSpec, with_coupon: bool) -> list[dict]:
    rules = [
        _rule("title", "商品标题", "text", "h1.goods-name", site.title),
        _rule("list_price", "标价", "price", "span.price-origin", site.list_price, "标价"),
        _rule("promo_price", "到手价", "price", "span.price-promo", site.promo_price, "到手价"),
    ]
    if with_coupon:
        rules.append(_rule("coupon_price", "券后价", "price", "div.coupon-site span", site.coupon_price, "券后价"))
    rules.extend([
        _rule("stock", "库存状态", "stock", "span.stock-state", site.stock),
        _rule("reviews", "评价数", "count", "span.review-count", site.reviews.replace(",", ""), None, COUNT_REGEX),
        _rule("sku", "SKU 编码", "text", "div.sku-label", site.sku),
    ])
    return rules


DRAFT_RULES = [
    _rule("title", "商品标题", "text", "h1.goods-name", "待补充标题模板"),
    _rule("promo_price", "到手价", "price", "span.price-promo", "待补充到手价", "到手价"),
    _rule("stock", "库存状态", "stock", "span.stock-state", "待补充库存"),
]


def site_by_key(key: str) -> SiteSpec:
    for site in SITES:
        if site.key == key:
            return site
    raise KeyError(key)
