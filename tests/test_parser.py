"""Tests for the CorpAI role file parser."""

import pytest
from pathlib import Path
import tempfile
import os

from corpai.parser import parse_role_file
from corpai.models import RankLevel


SAMPLE_ROLE = """# [L5] CEO — Chief Executive Officer

---

## Identity

| Field | Value |
|---|---|
| **Rank** | L5 — Executive |
| **Reports to** | OWNER |
| **Direct reports** | CFO, CTO, COO, CMO |
| **Domain** | Entire organization |

---

## Responsibilities

- Translate the OWNER's mission into organizational strategy
- Delegate strategic objectives to L5 domain executives
- Monitor organization-wide health and output

---

## Authority

- May delegate to any agent L1–L5

---

## Escalation Triggers

| Trigger | Priority | Action |
|---|---|---|
| Any L5 executive escalates unresolved | P1 | Escalate to OWNER |

---

## Communication Patterns

```
Receives: TASK, OVERRIDE from OWNER
Sends: TASK to CFO, CTO, COO, CMO
```

---

## Optional Personality Template

```yaml
personality:
  tone: decisive, visionary
```
"""


def write_temp_role(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def test_parse_rank():
    path = write_temp_role(SAMPLE_ROLE)
    try:
        role = parse_role_file(path)
        assert role.rank == RankLevel.L5
    finally:
        os.unlink(path)


def test_parse_title():
    path = write_temp_role(SAMPLE_ROLE)
    try:
        role = parse_role_file(path)
        assert role.title == "CEO"
    finally:
        os.unlink(path)


def test_parse_reports_to():
    path = write_temp_role(SAMPLE_ROLE)
    try:
        role = parse_role_file(path)
        assert role.reports_to == "OWNER"
    finally:
        os.unlink(path)


def test_parse_direct_reports():
    path = write_temp_role(SAMPLE_ROLE)
    try:
        role = parse_role_file(path)
        assert len(role.direct_reports) == 4
        assert "CFO" in role.direct_reports
    finally:
        os.unlink(path)


def test_parse_responsibilities():
    path = write_temp_role(SAMPLE_ROLE)
    try:
        role = parse_role_file(path)
        assert len(role.responsibilities) == 3
    finally:
        os.unlink(path)


def test_parse_has_personality():
    path = write_temp_role(SAMPLE_ROLE)
    try:
        role = parse_role_file(path)
        assert role.has_personality is True
    finally:
        os.unlink(path)


def test_parse_missing_personality():
    content = SAMPLE_ROLE.replace("## Optional Personality Template", "## Notes")
    path = write_temp_role(content)
    try:
        role = parse_role_file(path)
        assert role.has_personality is False
    finally:
        os.unlink(path)
