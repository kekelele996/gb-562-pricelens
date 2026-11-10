"""确定性快照 HTML 生成器（标准库，无随机）。

seed_demo.py 用它生成 6 个站点的 baseline / new 快照；算法 A/B 的输入就是这些 HTML，
因此 drift_score 与候选置信度都是真算出来的，不写死。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SiteSpec:
    key: str
    name: str
    domain: str
    market: str
    robots_policy: str
    qps_limit: float
    status: str
    priority: int
    title: str
    list_price: str
    promo_price: str
    promo_price_new: str
    coupon_price: str
    stock: str
    reviews: str
    reviews_new: str
    sku: str
    brand: str
    drift_level: str          # none / low / medium / high / challenge
    diagnose: bool
    extra_fields: list[dict] = field(default_factory=list)


def _money(value: str) -> str:
    return f"¥{value}"


def page_baseline(site: SiteSpec) -> str:
    reviews_badge = f"好评率 98%"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{site.title} - {site.name}</title></head>
<body class="site-{site.key}">
<header class="site-head"><div class="brand">{site.name}</div><nav class="site-nav"><a href="/">首页</a><a href="/list">全部商品</a></nav></header>
<main class="goods-detail">
  <section class="gallery"><img class="goods-img" src="/img/{site.sku}.jpg" alt="{site.title}"/><div class="thumbs"><img class="thumb" src="/img/t1.jpg"/><img class="thumb" src="/img/t2.jpg"/></div></section>
  <section class="goods-info">
    <h1 class="goods-name">{site.title}</h1>
    <div class="goods-tags"><span class="tag">自营</span><span class="tag">次日达</span></div>
    <div class="price-block">
      <dl class="price-line"><dt>标价</dt><dd><span class="price-origin">{_money(site.list_price)}</span></dd></dl>
      <dl class="price-line"><dt>到手价</dt><dd><span class="price-promo">{_money(site.promo_price)}</span></dd></dl>
    </div>
    <div class="coupon-site"><span class="coupon-rule">满2000减300</span><span class="coupon-label">券后价</span><span class="coupon-amount">{_money(site.coupon_price)}</span></div>
    <div class="stock-line"><span class="stock-state">{site.stock}</span></div>
    <div class="sku-line"><div class="sku-label">{site.sku}</div></div>
    <div class="review-block"><span class="review-count">{reviews_badge}</span><span class="review-num">{site.reviews} 条评价</span></div>
  </section>
</main>
<footer class="site-foot"><p>{site.name} · {site.market} · 客服 400-000-0000</p></footer>
</body></html>"""


def page_new_high(site: SiteSpec) -> str:
    """改版页：保留主骨架，定向做 class 改名 + 结构插入 + 侧栏诱饵节点。

    真实漂移就来自这些改动：旧选择器命中侧栏诱饵（静默错位）或直接 miss。
    """
    reviews_badge = "好评率 98%"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{site.title} - {site.name} 新版</title></head>
<body class="site-{site.key}">
<header class="site-head"><div class="brand">{site.name}</div><nav class="site-nav"><a href="/">首页</a><a href="/list">全部商品</a></nav><form class="search-bar"><input class="search-input" name="q"/></form></header>
<main class="goods-detail">
  <section class="gallery"><img class="goods-img" src="/img/{site.sku}.jpg" alt="{site.title}"/><div class="thumbs"><img class="thumb" src="/img/t1.jpg"/><img class="thumb" src="/img/t2.jpg"/></div><div class="media-tags"><span class="tag">自营</span><span class="tag">闪电达</span></div></section>
  <section class="goods-info">
    <h1 class="product-title">{site.title}（2026款）</h1>
    <div class="goods-tags"><span class="tag">自营</span><span class="tag">次日达</span></div>
    <div class="price-block">
      <dl class="price-line"><dt>标价</dt><dd><span class="price-origin">{_money(site.list_price)}</span></dd></dl>
      <dl class="price-line"><dt>到手价</dt><dd><span class="price-now">{_money(site.promo_price_new)}</span></dd></dl>
    </div>
    <div class="coupon-zone"><span class="coupon-label">券后价</span><span class="coupon-value">{_money(site.coupon_price)}</span></div>
    <div class="stock-line"><span class="stock-state">{site.stock}</span></div>
    <div class="sku-line"><div class="sku-label">{site.sku}</div></div>
    <div class="review-stat"><b>{site.reviews_new}</b><em class="stat-unit">条评价</em></div>
    <div class="service-line"><span class="service-item">7天无理由</span><span class="service-item">上门取件</span><span class="service-item">以旧换新</span><span class="service-item">送装一体</span></div>
  </section>
  <aside class="reco-side">
    <h1 class="goods-name">猜你喜欢｜九阳豆浆机 DJ13</h1>
    <div class="promo-banner"><span class="price-promo">满2000减300</span></div>
    <ul class="reco-list"><li class="reco-item">推荐商品 1</li><li class="reco-item">推荐商品 2</li><li class="reco-item">推荐商品 3</li></ul>
  </aside>
</main>
<footer class="site-foot"><p>{site.name} · {site.market} · 客服 400-000-0000</p><div class="foot-links"><a href="/help">帮助</a><a href="/about">关于</a></div></footer>
</body></html>"""


def page_new_medium(site: SiteSpec) -> str:
    """中度改版：商品标题容器、价格块包装、评论结构与少量新模块变化。"""
    reviews_badge = "好评率 98%"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{site.title} - {site.name}</title></head>
<body class="site-{site.key}">
<header class="site-head"><div class="brand">{site.name}</div><nav class="site-nav"><a href="/">首页</a><a href="/list">全部商品</a></nav></header>
<main class="goods-detail">
  <section class="gallery"><img class="goods-img" src="/img/{site.sku}.jpg" alt="{site.title}"/><div class="thumbs"><img class="thumb" src="/img/t1.jpg"/><img class="thumb" src="/img/t2.jpg"/></div></section>
  <section class="goods-info">
    <div class="title-wrap"><h1 class="product-title">{site.title}</h1></div>
    <div class="goods-tags"><span class="tag">自营</span><span class="tag">次日达</span></div>
    <div class="price-panel">
      <dl class="price-line"><dt>标价</dt><dd><span class="price-origin">{_money(site.list_price)}</span></dd></dl>
      <dl class="price-line"><dt>到手价</dt><dd><span class="price-current">{_money(site.promo_price_new)}</span></dd></dl>
    </div>
    <div class="coupon-site"><span class="coupon-rule">满2000减300</span><span class="coupon-label">券后价</span><span class="coupon-amount">{_money(site.coupon_price)}</span></div>
    <div class="stock-line"><span class="stock-state">{site.stock}</span></div>
    <div class="sku-line"><div class="sku-label">{site.sku}</div></div>
    <div class="review-stat"><b>{site.reviews_new}</b><em class="stat-unit">条评价</em></div>
    <div class="notice-box"><span class="notice">价格随促销活动浮动，以结算页为准</span></div>
    <div class="service-line"><span class="service-item">7天无理由</span></div>
  </section>
</main>
<footer class="site-foot"><p>{site.name} · {site.market} · 客服 400-000-0000</p></footer>
</body></html>"""


def page_new_low(site: SiteSpec) -> str:
    """轻度改版：只新增活动横幅、相关商品与页脚链接，原选择器仍可用。"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{site.title} - {site.name}</title></head>
<body class="site-{site.key}">
<header class="site-head"><div class="brand">{site.name}</div><nav class="site-nav"><a href="/">首页</a><a href="/list">全部商品</a></nav></header>
<div class="campaign-banner"><span class="campaign-text">双十一预售开启</span><a class="campaign-link" href="/campaign">立即查看</a></div>
<main class="goods-detail">
  <section class="gallery"><img class="goods-img" src="/img/{site.sku}.jpg" alt="{site.title}"/><div class="thumbs"><img class="thumb" src="/img/t1.jpg"/></div></section>
  <section class="goods-info">
    <h1 class="goods-name">{site.title}</h1>
    <div class="goods-tags"><span class="tag">自营</span><span class="tag">次日达</span></div>
    <div class="price-block">
      <dl class="price-line"><dt>标价</dt><dd><span class="price-origin">{_money(site.list_price)}</span></dd></dl>
      <dl class="price-line"><dt>到手价</dt><dd><span class="price-promo">{_money(site.promo_price_new)}</span></dd></dl>
    </div>
    <div class="coupon-site"><span class="coupon-rule">满2000减300</span><span class="coupon-label">券后价</span><span class="coupon-amount">{_money(site.coupon_price)}</span></div>
    <div class="stock-line"><span class="stock-state">{site.stock}</span></div>
    <div class="sku-line"><div class="sku-label">{site.sku}</div></div>
    <div class="review-block"><span class="review-count">{site.reviews} 条评价</span><span class="review-num">{site.reviews} 条评价</span></div>
  </section>
  <aside class="related-box"><h2 class="related-title">相关商品</h2><ul class="related-list"><li class="related-item">相关 1</li><li class="related-item">相关 2</li></ul></aside>
</main>
<footer class="site-foot"><p>{site.name} · {site.market} · 客服 400-000-0000</p><div class="foot-links"><a href="/help">帮助中心</a><a href="/service">售后服务</a><a href="/about">关于我们</a></div></footer>
</body></html>"""


def page_challenge(site: SiteSpec) -> str:
    """反爬校验页：无商品节点，用于演示「批次失败」与告警缺失的场景。"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>安全校验 - {site.name}</title></head>
<body class="challenge-page"><div class="challenge-box"><h1 class="challenge-title">访问过于频繁</h1><p class="challenge-text">请完成安全校验后继续访问</p><button class="challenge-btn">点击校验</button></div></body></html>"""


SITES: list[SiteSpec] = [
    SiteSpec("jingxuan", "京选超市", "jingxuan.example.com", "华东", "allow", 2.0, "active", 1,
             "京选壹号 智能电饭煲 4L 钛金内胆", "3,299.00", "2,849.00", "2,699.00", "2,599.00",
             "现货", "1,284", "1284", "JX-DFB40-T1", "京选", "high", True),
    SiteSpec("taohuasuan", "淘划算", "taohuasuan.example.com", "全国", "partial", 1.5, "active", 2,
             "南极人 加厚保暖内衣套装 男士", "299.00", "259.00", "239.00", "219.00",
             "现货", "4,216", "4216", "NJR-NK-2026", "南极人", "high", True),
    SiteSpec("pinyigou", "拼易购", "pinyigou.example.com", "华南", "allow", 1.0, "active", 3,
             "美的 电热水壶 1.7L 304不锈钢", "129.00", "99.00", "89.00", "79.00",
             "预售", "8,832", "8832", "MD-SH17-304", "美的", "medium", True),
    SiteSpec("suningkuaigou", "苏宁快购", "suningkuaigou.example.com", "华北", "partial", 1.0, "active", 4,
             "海尔 10公斤 滚筒洗衣机", "2,599.00", "2,199.00", "2,099.00", "1,999.00",
             "现货", "15,200", "15200", "HR-10KG-X1", "海尔", "low", True),
    SiteSpec("doudian", "抖店商城", "doudian.example.com", "全国", "blocked", 0.5, "active", 5,
             "小熊 电煮锅 2L 学生宿舍", "169.00", "139.00", "129.00", "119.00",
             "现货", "3,021", "3021", "XX-DZG-2L", "小熊", "challenge", False),
    SiteSpec("xhsgoods", "小红书好物", "xhsgoods.example.com", "华东", "partial", 0.5, "paused", 6,
             "添可 无线洗地机 2.0", "3,699.00", "2,999.00", "2,899.00", "2,799.00",
             "缺货", "765", "765", "TINECO-FW20", "添可", "none", False),
]


def build_snapshot_html(site: SiteSpec, variant: str) -> str:
    if variant == "baseline":
        return page_baseline(site)
    level = site.drift_level
    if level == "high":
        return page_new_high(site)
    if level == "medium":
        return page_new_medium(site)
    if level == "low":
        return page_new_low(site)
    if level == "challenge":
        return page_challenge(site)
    # none：只加一行构建注释，保证 dom_hash 不同但结构不变
    return page_baseline(site).replace("<body ", "<!-- build 20261110 -->\n<body ")


def snapshot_url(site: SiteSpec) -> str:
    return f"https://{site.domain}/item/{site.sku.lower()}"


if __name__ == "__main__":
    from src.services.drift_detector import diagnose  # noqa: F401 - 调试用
