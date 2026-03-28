"""Generate org charts from CorpAI role files."""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from .models import Role, RankLevel, OrgNode, RANK_NAMES
from .parser import load_roles_from_dir


RANK_COLORS = {
    RankLevel.OWNER:  "#1a1a2e",
    RankLevel.L5:     "#16213e",
    RankLevel.L4:     "#0f3460",
    RankLevel.L3:     "#533483",
    RankLevel.L2:     "#2b6cb0",
    RankLevel.L1:     "#2d6a4f",
}


def _normalize(s: str) -> str:
    """Normalize a role title for matching."""
    s = re.sub(r"\[l\d\]\s*", "", s.strip().lower())
    s = re.sub(r"\(.*?\)", "", s).strip()
    return s


def build_org_tree(roles: list[Role]) -> dict[str, OrgNode]:
    """Build a tree of OrgNodes from a flat list of roles."""
    nodes: dict[str, OrgNode] = {}

    for role in roles:
        key = _normalize(role.title)
        nodes[key] = OrgNode(role=role)

    # Wire up parent-child relationships
    for role in roles:
        if role.rank == RankLevel.OWNER:
            continue
        child_node = nodes.get(_normalize(role.title))
        if not child_node:
            continue
        parent_key = _normalize(role.reports_to)
        parent_node = nodes.get(parent_key)
        if parent_node:
            parent_node.children.append(child_node)
            child_node.parent = parent_node

    return nodes


def generate_mermaid(roles_dir: Path, department: Optional[str] = None) -> str:
    """Generate Mermaid graph syntax for the org."""
    roles = load_roles_from_dir(roles_dir)

    if department:
        roles = [r for r in roles if r.department.lower() == department.lower()]

    nodes = build_org_tree(roles)
    lines = ["graph TD"]

    seen_edges: set[tuple[str, str]] = set()

    def node_id(title: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "_", title.upper())

    def node_label(role: Role) -> str:
        rank_str = role.rank.name if role.rank else "?"
        return f'["{rank_str}: {role.title}"]'

    for key, node in nodes.items():
        nid = node_id(node.role.title)
        label = node_label(node.role)
        lines.append(f"    {nid}{label}")

    lines.append("")

    for key, node in nodes.items():
        parent = node.parent
        if parent:
            src = node_id(parent.role.title)
            dst = node_id(node.role.title)
            edge = (src, dst)
            if edge not in seen_edges:
                lines.append(f"    {src} --> {dst}")
                seen_edges.add(edge)

    return "\n".join(lines)


def generate_ascii_tree(roles_dir: Path, department: Optional[str] = None) -> str:
    """Generate an ASCII org tree."""
    roles = load_roles_from_dir(roles_dir)

    if department:
        roles = [r for r in roles if r.department.lower() == department.lower()]

    nodes = build_org_tree(roles)

    # Find roots (nodes with no parent)
    roots = [n for n in nodes.values() if n.parent is None]
    # Sort roots by rank descending
    roots.sort(key=lambda n: -(n.role.rank.value if n.role.rank else 0))

    lines: list[str] = []

    def render_node(node: OrgNode, prefix: str = "", is_last: bool = True) -> None:
        connector = "└── " if is_last else "├── "
        rank_str = node.role.rank.name if node.role.rank else "??"
        rank_label = RANK_NAMES.get(node.role.rank, "")
        dept = node.role.department
        lines.append(f"{prefix}{connector}[{rank_str}] {node.role.title}  ({dept})")

        child_prefix = prefix + ("    " if is_last else "│   ")
        sorted_children = sorted(
            node.children,
            key=lambda n: -(n.role.rank.value if n.role.rank else 0)
        )
        for i, child in enumerate(sorted_children):
            render_node(child, child_prefix, i == len(sorted_children) - 1)

    for i, root in enumerate(roots):
        render_node(root, "", i == len(roots) - 1)

    return "\n".join(lines)
