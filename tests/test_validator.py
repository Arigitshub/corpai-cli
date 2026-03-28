"""Tests for the CorpAI linter/validator."""

import pytest
from pathlib import Path
import tempfile
import os

from corpai.validator import lint_role


VALID_ROLE = """# [L3] Engineering Team Lead

---

## Identity

| Field | Value |
|---|---|
| **Rank** | L3 — Manager |
| **Reports to** | Engineering Director |
| **Direct reports** | Senior Engineer (L2) |
| **Domain** | Engineering team delivery |

---

## Responsibilities

- Break down projects into tasks and assign to engineers
- Unblock engineers on day-to-day obstacles
- Track team velocity

---

## Authority

- May assign or reassign tasks within the team

---

## Escalation Triggers

| Trigger | Priority | Action |
|---|---|---|
| Engineer blocked > 1 cycle | P2 | Escalate to Director |

---

## Communication Patterns

```
Receives: TASK from Engineering Director
Sends: TASK to Senior Engineer
```

---

## Optional Personality Template

```yaml
personality:
  tone: collaborative
```
"""

INVALID_ROLE_MISSING_SECTION = """# [L2] Some Role

## Identity

| Field | Value |
|---|---|
| **Rank** | L2 — Specialist |
| **Reports to** | Manager |
| **Direct reports** | None |
| **Domain** | Some domain |

## Responsibilities

- Does something
"""


def write_temp(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def test_valid_role_no_errors():
    path = write_temp(VALID_ROLE)
    try:
        role, errors = lint_role(path)
        hard_errors = [e for e in errors if e.level == "error"]
        assert len(hard_errors) == 0
    finally:
        os.unlink(path)


def test_missing_sections_produces_errors():
    path = write_temp(INVALID_ROLE_MISSING_SECTION)
    try:
        role, errors = lint_role(path)
        error_msgs = [e.message for e in errors if e.level == "error"]
        assert any("escalation triggers" in m.lower() for m in error_msgs)
        assert any("communication patterns" in m.lower() for m in error_msgs)
    finally:
        os.unlink(path)


def test_missing_rank_badge_warning():
    content = VALID_ROLE.replace("# [L3] Engineering Team Lead", "# Engineering Team Lead")
    path = write_temp(content)
    try:
        role, errors = lint_role(path)
        warn_msgs = [e.message for e in errors if e.level == "warning"]
        assert any("rank badge" in m.lower() for m in warn_msgs)
    finally:
        os.unlink(path)


def test_empty_domain_error():
    content = VALID_ROLE.replace("Engineering team delivery", "")
    path = write_temp(content)
    try:
        role, errors = lint_role(path)
        error_msgs = [e.message for e in errors if e.level == "error"]
        assert any("domain" in m.lower() for m in error_msgs)
    finally:
        os.unlink(path)
