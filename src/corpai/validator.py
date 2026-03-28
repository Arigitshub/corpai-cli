"""Lint and validate CorpAI role files against the spec."""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from .models import (
    Role, RankLevel, LintError,
    REQUIRED_SECTIONS, REQUIRED_IDENTITY_FIELDS,
)
from .parser import parse_role_file, load_roles_from_dir


def _err(path: Path, msg: str, field: Optional[str] = None) -> LintError:
    return LintError(path=path, level="error", message=msg, field=field)


def _warn(path: Path, msg: str, field: Optional[str] = None) -> LintError:
    return LintError(path=path, level="warning", message=msg, field=field)


def lint_role(path: Path) -> tuple[Optional[Role], list[LintError]]:
    """Validate a single role file. Returns (role, errors)."""
    errors: list[LintError] = []

    try:
        role = parse_role_file(path)
    except Exception as e:
        return None, [_err(path, f"Could not parse file: {e}")]

    # OWNER is the human principal — exempt from agent-spec checks
    if role.rank and role.rank.name == "OWNER" or role.title.upper() == "OWNER":
        return role, []

    sections = {k.lower() for k in role.raw_sections}

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(_err(path, f"Missing required section: ## {section.title()}", section))

    # Check rank is parseable
    if role.rank is None:
        errors.append(_err(path, "Could not determine rank level (expected [L1]–[L5] or OWNER in title)", "rank"))

    # Check title format
    content = path.read_text(encoding="utf-8")
    first_heading = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    if first_heading:
        heading = first_heading.group(1)
        if not re.match(r"\[(L[1-5]|OWNER)\]", heading, re.IGNORECASE):
            errors.append(_warn(path, f'Title "{heading}" missing rank badge — expected format: [L5] Role Title', "title"))

    # Check reports_to is set
    if not role.reports_to or role.reports_to in ("—", "-"):
        if role.rank != RankLevel.OWNER:
            errors.append(_err(path, '"Reports to" field is empty', "reports to"))

    # Check domain is set
    if not role.domain or role.domain in ("—", "-", "{Area of responsibility}"):
        errors.append(_err(path, '"Domain" field is empty or still a template placeholder', "domain"))

    # Check responsibilities has at least one item
    if not role.responsibilities:
        errors.append(_err(path, '"Responsibilities" section has no bullet items', "responsibilities"))

    # Check communication patterns section has content
    comm_section = role.raw_sections.get("communication patterns", "")
    if not comm_section.strip():
        errors.append(_err(path, '"Communication Patterns" section is empty', "communication patterns"))

    # Check escalation triggers table has at least one row
    esc_section = role.raw_sections.get("escalation triggers", "")
    table_rows = [l for l in esc_section.splitlines()
                  if l.strip().startswith("|") and "---" not in l and "trigger" not in l.lower()]
    if not table_rows:
        errors.append(_warn(path, '"Escalation Triggers" table has no entries', "escalation triggers"))

    # Warn if no personality template
    if not role.has_personality:
        errors.append(_warn(path, "No optional personality template found", "personality"))

    return role, errors


def lint_org(roles_dir: Path) -> tuple[list[Role], list[LintError]]:
    """Lint all roles in a directory and check cross-role consistency."""
    all_errors: list[LintError] = []
    all_roles: list[Role] = []

    md_files = sorted(roles_dir.rglob("*.md"))

    for md_file in md_files:
        if md_file.name.upper() in ("README.MD",):
            continue
        role, errors = lint_role(md_file)
        all_errors.extend(errors)
        if role:
            all_roles.append(role)

    # Cross-role checks
    role_titles = {r.title.lower() for r in all_roles}
    role_titles.add("owner")  # OWNER is always implicitly present

    for role in all_roles:
        if role.rank == RankLevel.OWNER:
            continue
        reports_to_clean = re.sub(r"\(.*?\)", "", role.reports_to).strip().lower()
        # Strip rank badge if present
        reports_to_clean = re.sub(r"\[l\d\]\s*", "", reports_to_clean).strip()

        if reports_to_clean and reports_to_clean not in role_titles:
            all_errors.append(_warn(
                role.path,
                f'"Reports to" references "{role.reports_to}" — no matching role found in org',
                "reports to"
            ))

    return all_roles, all_errors
