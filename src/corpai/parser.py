"""Parse CorpAI role markdown files into Role objects."""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from .models import Role, RankLevel


def _extract_heading_sections(content: str) -> dict[str, str]:
    """Split markdown into sections by ## headings."""
    sections: dict[str, str] = {}
    current_heading = "__preamble__"
    current_lines: list[str] = []

    for line in content.splitlines():
        match = re.match(r"^#{1,3}\s+(.+)", line)
        if match:
            sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = match.group(1).strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_heading] = "\n".join(current_lines).strip()
    return sections


def _parse_md_table(text: str) -> dict[str, str]:
    """Parse a markdown table into a key→value dict (first two cols)."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        parts = [p.strip().strip("*") for p in line.strip("|").split("|")]
        if len(parts) >= 2:
            key = parts[0].lower().strip("*").strip()
            val = parts[1].strip()
            result[key] = val
    return result


def _parse_bullet_list(text: str) -> list[str]:
    """Extract bullet list items from markdown text."""
    items = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            items.append(line[2:].strip())
    return items


def _parse_title(content: str) -> tuple[str, Optional[RankLevel]]:
    """Extract role title and rank from the first # heading."""
    match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    if not match:
        return "Unknown", None

    heading = match.group(1).strip()

    # Format: [L5] CEO — Chief Executive Officer
    rank_match = re.match(r"\[([Ll]\d|OWNER)\]\s+(.+?)(?:\s+—.*)?$", heading)
    if rank_match:
        rank_str = rank_match.group(1).upper()
        title = rank_match.group(2).strip()
        rank = RankLevel.from_string(rank_str)
        return title, rank

    # Format: OWNER — Human Principal
    if heading.upper().startswith("OWNER"):
        return "OWNER", RankLevel.OWNER

    return heading, None


def parse_role_file(path: Path) -> Role:
    """Parse a role .md file into a Role object."""
    content = path.read_text(encoding="utf-8")
    sections = _extract_heading_sections(content)

    title, rank = _parse_title(content)

    # Parse identity table
    identity_section = sections.get("identity", "")
    identity = _parse_md_table(identity_section)

    reports_to = identity.get("reports to", "").strip()
    domain = identity.get("domain", "").strip()

    # Direct reports — could be comma list or "None"
    raw_reports = identity.get("direct reports", "None")
    if raw_reports.lower() in ("none", "—", "-", ""):
        direct_reports = []
    else:
        direct_reports = [r.strip() for r in re.split(r"[,;]", raw_reports) if r.strip()]

    responsibilities = _parse_bullet_list(sections.get("responsibilities", ""))

    # Department = parent folder name
    department = path.parent.name

    has_personality = "optional personality template" in sections

    return Role(
        path=path,
        title=title,
        rank=rank,
        reports_to=reports_to,
        direct_reports=direct_reports,
        domain=domain,
        department=department,
        responsibilities=responsibilities,
        has_personality=has_personality,
        raw_sections=sections,
    )


def load_roles_from_dir(roles_dir: Path) -> list[Role]:
    """Recursively load all role .md files from a directory."""
    roles = []
    for md_file in sorted(roles_dir.rglob("*.md")):
        # Skip non-role files
        if md_file.name.upper() in ("README.MD", "CONTRIBUTING.MD"):
            continue
        try:
            roles.append(parse_role_file(md_file))
        except Exception:
            pass  # malformed files caught by linter
    return roles
