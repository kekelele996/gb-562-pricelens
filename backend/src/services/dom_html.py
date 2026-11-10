"""轻量 HTML 解析与选择器引擎（标准库 html.parser，无第三方依赖）。

支持的 CSS 子集：
  - `tag` / `*`
  - `.class` / `tag.class1.class2`
  - `#id`
  - `[attr=value]` / `[class^=price]`
  - 后代组合（空格），以及 `:nth-of-type(n)` 后缀
支持的 XPath 子集（仅算法 B 的文本锚点候选使用）：
  xpath://TAG[contains(text(),'ANCHOR')]/following-sibling::TAG[N]
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from html.parser import HTMLParser

_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
SPACE_RE = re.compile(r"\s+")


def normalize(text: str | None) -> str:
    if not text:
        return ""
    return SPACE_RE.sub(" ", text.replace("\u3000", " ")).strip()


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    parent: "Node | None" = None
    children: list["Node"] = field(default_factory=list)
    order: int = 0
    depth: int = 0

    def classes(self) -> list[str]:
        return [c for c in self.attrs.get("class", "").split(" ") if c]

    def own_text(self) -> str:
        return ""

    def text(self) -> str:
        parts: list[str] = []

        def walk(node: Node) -> None:
            if node.tag == "#text":
                parts.append(node.attrs.get("value", ""))
                return
            for child in node.children:
                walk(child)

        walk(self)
        return normalize(" ".join(parts))

    def siblings(self) -> list["Node"]:
        if not self.parent:
            return []
        return self.parent.children

    def index_of_type(self) -> int:
        same = [n for n in self.siblings() if n.tag == self.tag]
        return same.index(self) + 1 if self in same else 0


class _Builder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.current = self.root
        self.counter = 0

    def _append(self, node: Node) -> None:
        node.parent = self.current
        node.depth = self.current.depth + 1
        self.counter += 1
        node.order = self.counter
        self.current.children.append(node)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag.lower(), {k: (v or "") for k, v in attrs})
        self._append(node)
        if tag.lower() not in _VOID_TAGS:
            self.current = node

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag.lower(), {k: (v or "") for k, v in attrs})
        self._append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        node = self.current
        while node is not self.root and node.tag != tag:
            node = node.parent or self.root
        if node is not self.root and node.parent is not None:
            self.current = node.parent

    def handle_data(self, data: str) -> None:
        if data.strip():
            text_node = Node("#text", {"value": data})
            self._append(text_node)


def parse_html(html: str) -> Node:
    builder = _Builder()
    builder.feed(html or "")
    builder.close()
    return builder.root


def iter_nodes(root: Node):
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(node.children))


def all_text(root: Node) -> str:
    return root.text()


def _match_simple(node: Node, token: str) -> bool:
    if node.tag == "#text" or node.tag == "#root":
        return False
    nth = None
    nth_match = re.search(r":nth-of-type\((\d+)\)$", token)
    if nth_match:
        nth = int(nth_match.group(1))
        token = token[: nth_match.start()]
    attr_matches = re.findall(r"\[([a-zA-Z0-9_:-]+)(?:([\^$*]?=)'?([^\]']*)'?)?\]", token)
    token = re.sub(r"\[[^\]]+\]", "", token)
    id_matches = re.findall(r"#([\w-]+)", token)
    token = re.sub(r"#[\w-]+", "", token)
    classes = re.findall(r"\.([\w-]+)", token)
    token = re.sub(r"\.[\w-]+", "", token)
    tag = token.strip()
    if tag and tag != "*" and node.tag != tag:
        return False
    node_classes = set(node.classes())
    if classes and not set(classes).issubset(node_classes):
        return False
    if id_matches and node.attrs.get("id") not in id_matches:
        return False
    for name, op, expected in attr_matches:
        actual = node.attrs.get(name, "")
        if op == "^=" and not actual.startswith(expected):
            return False
        if op == "$=" and not actual.endswith(expected):
            return False
        if op == "*=" and expected not in actual:
            return False
        if not op and actual != expected:
            return False
    if nth is not None and node.index_of_type() != nth:
        return False
    return True


def select(root: Node, selector: str) -> list[Node]:
    """选择器求值：后代组合 + 简单选择器。"""
    selector = (selector or "").strip()
    if not selector:
        return []
    tokens = [t for t in selector.split() if t]
    candidates = [n for n in iter_nodes(root) if _match_simple(n, tokens[-1])]
    for token in reversed(tokens[:-1]):
        filtered = []
        for node in candidates:
            parent = node.parent
            while parent is not None:
                if _match_simple(parent, token):
                    filtered.append(node)
                    break
                parent = parent.parent
        candidates = filtered
    return sorted(candidates, key=lambda n: n.order)


def text_anchor(root: Node, expr: str) -> list[Node]:
    """解析受限 XPath：//TAG[contains(text(),'ANCHOR')]/following-sibling::TAG[N]。"""
    pattern = re.compile(
        r"^xpath://(?P<tag>[\w*]+)\[contains\(text\(\),'(?P<anchor>[^']+)'\)\]"
        r"/following-sibling::(?P<target>[\w*]+)\[(?P<index>\d+)\]$"
    )
    match = pattern.match(expr.strip())
    if not match:
        return []
    anchor = match.group("anchor")
    tag_filter = match.group("tag")
    target_tag = match.group("target")
    index = int(match.group("index"))
    result: list[Node] = []
    for node in iter_nodes(root):
        if node.tag == "#text":
            continue
        if tag_filter != "*" and node.tag != tag_filter:
            continue
        if anchor not in node.text():
            continue
        siblings = [s for s in node.siblings() if s.tag != "#text"]
        try:
            position = siblings.index(node)
        except ValueError:
            continue
        following = siblings[position + 1:]
        for sibling in following:
            if target_tag != "*" and sibling.tag != target_tag:
                continue
            hit = sibling
            if index > 1:
                extras = [
                    s for s in following[following.index(sibling):]
                    if target_tag == "*" or s.tag == target_tag
                ]
                if len(extras) < index:
                    continue
                hit = extras[index - 1]
            result.append(hit)
            break
    return result


def fuzzy_scan(root: Node, tag: str, expected: str) -> list[tuple[Node, float]]:
    """按 tag 扫描全部节点，按文本与 expected 的相似度降序返回。"""
    scored: list[tuple[Node, float]] = []
    for node in iter_nodes(root):
        if node.tag == "#text":
            continue
        if tag != "*" and node.tag != tag:
            continue
        text = node.text()
        if not text:
            continue
        ratio = SequenceMatcher(None, normalize(text), normalize(expected)).ratio()
        scored.append((node, ratio))
    scored.sort(key=lambda item: (-item[1], item[0].order))
    return scored


def path_signature(node: Node) -> str:
    """祖先 tag/class 链签名（深度上限 6，用于漂移路径 Jaccard）。"""
    parts: list[str] = []
    current: Node | None = node
    while current is not None and current.tag not in {"#root", "#text"}:
        classes = ".".join(sorted(current.classes())[:2])
        parts.append(f"{current.tag}{'.' + classes if classes else ''}")
        current = current.parent
    return ">".join(reversed(parts[-6:]))


def path_multiset(root: Node) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in iter_nodes(root):
        if node.tag in {"#root", "#text"}:
            continue
        sig = path_signature(node)
        counts[sig] = counts.get(sig, 0) + 1
    return counts


def node_count(root: Node) -> int:
    return sum(1 for n in iter_nodes(root) if n.tag not in {"#root", "#text"})


def group_changed_subtrees(baseline_paths: dict[str, int], new_paths: dict[str, int]) -> list[dict]:
    """按祖先前两级分组统计新增/缺失路径，供 top_changed_subtrees。"""
    groups: dict[str, dict] = {}
    for sig, count in new_paths.items():
        base = baseline_paths.get(sig, 0)
        if count > base:
            key = ">".join(sig.split(">")[:2])
            entry = groups.setdefault(key, {"path": key, "added": 0, "removed": 0, "fields": []})
            entry["added"] += count - base
    for sig, count in baseline_paths.items():
        new = new_paths.get(sig, 0)
        if count > new:
            key = ">".join(sig.split(">")[:2])
            entry = groups.setdefault(key, {"path": key, "added": 0, "removed": 0, "fields": []})
            entry["removed"] += count - new
    ordered = sorted(
        groups.values(),
        key=lambda g: (-(g["added"] + g["removed"]), g["path"]),
    )
    return ordered[:8]
