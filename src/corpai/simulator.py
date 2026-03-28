"""Simulate message flows through a CorpAI org hierarchy."""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from .models import Role, RankLevel, MessageType, Priority, SimMessage
from .parser import load_roles_from_dir
from .graph import build_org_tree, _normalize, OrgNode


def _find_node(nodes: dict[str, OrgNode], query: str) -> Optional[OrgNode]:
    """Find a node by partial title match."""
    q = query.lower().strip()
    # Exact match first
    if q in nodes:
        return nodes[q]
    # Partial match
    for key, node in nodes.items():
        if q in key or q in node.role.title.lower():
            return node
    return None


def _get_chain_up(node: OrgNode) -> list[OrgNode]:
    """Get the chain from node up to root."""
    chain = []
    current = node
    while current:
        chain.append(current)
        current = current.parent
    return chain


def _get_chain_down(from_node: OrgNode, to_node: OrgNode) -> Optional[list[OrgNode]]:
    """Find the path from a higher node down to a lower node."""
    def dfs(current: OrgNode, target: OrgNode, path: list[OrgNode]) -> Optional[list[OrgNode]]:
        if current == target:
            return path + [current]
        for child in current.children:
            result = dfs(child, target, path + [current])
            if result:
                return result
        return None
    return dfs(from_node, to_node, [])


def simulate_task(
    roles_dir: Path,
    from_role: str,
    to_role: str,
    subject: str = "Execute assigned task",
    priority: str = "P3",
) -> list[SimMessage]:
    """
    Simulate a TASK message flowing from one role to another.
    Shows the full delegation chain.
    """
    roles = load_roles_from_dir(roles_dir)
    nodes = build_org_tree(roles)

    from_node = _find_node(nodes, from_role)
    to_node = _find_node(nodes, to_role)

    if not from_node:
        raise ValueError(f"Role not found: {from_role}")
    if not to_node:
        raise ValueError(f"Role not found: {to_role}")

    prio = Priority.from_string(priority) or Priority.P3
    messages: list[SimMessage] = []

    from_rank = from_node.role.rank.value if from_node.role.rank else 0
    to_rank = to_node.role.rank.value if to_node.role.rank else 0

    if from_rank >= to_rank:
        # Delegation: from flows down to target
        path = _get_chain_down(from_node, to_node)
        if not path:
            # Try going up to common ancestor then down
            from_chain = _get_chain_up(from_node)
            to_chain = _get_chain_up(to_node)
            from_set = {id(n): n for n in from_chain}
            common = next((n for n in to_chain if id(n) in from_set), None)
            if common:
                up_path = _get_chain_up(from_node)
                up_path = up_path[:up_path.index(common) + 1]
                down_path = _get_chain_down(common, to_node)
                path = up_path + (down_path[1:] if down_path else [])

        if path:
            for i in range(len(path) - 1):
                sender = path[i]
                receiver = path[i + 1]
                messages.append(SimMessage(
                    msg_type=MessageType.TASK,
                    from_role=sender.role.display_name,
                    to_role=receiver.role.display_name,
                    priority=prio,
                    subject=subject,
                    step=i + 1,
                ))
    else:
        # Escalation: from flows up to target
        path = _get_chain_up(from_node)
        target_idx = next(
            (i for i, n in enumerate(path) if _normalize(n.role.title) == _normalize(to_node.role.title)),
            None
        )
        if target_idx is not None:
            path = path[:target_idx + 1]

        for i in range(len(path) - 1):
            sender = path[i]
            receiver = path[i + 1]
            messages.append(SimMessage(
                msg_type=MessageType.ESCALATION,
                from_role=sender.role.display_name,
                to_role=receiver.role.display_name,
                priority=prio,
                subject=subject,
                step=i + 1,
            ))

    return messages


def simulate_escalation(
    roles_dir: Path,
    from_role: str,
    subject: str = "Blocked — cannot proceed",
    priority: str = "P1",
    stop_at: Optional[str] = None,
) -> list[SimMessage]:
    """Simulate an escalation chain from a role upward."""
    return simulate_task(
        roles_dir,
        from_role=from_role,
        to_role=stop_at or "owner",
        subject=subject,
        priority=priority,
    )
