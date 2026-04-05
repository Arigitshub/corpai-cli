"""Scaffold a new CorpAI org structure."""

from __future__ import annotations
from pathlib import Path
from rich.console import Console

console = Console()

BASIC_ROLE_TEMPLATE = """# [{rank}] {title}

> {description}

## Identity

| Field | Value |
|---|---|
| **Rank** | {rank} |
| **Department** | {department} |
| **Reports to** | {reports_to} |
| **Domain** | {domain} |

## Responsibilities
- {responsibility}

## Communication Patterns
```
{comm_patterns}
```

## Escalation Triggers
| Trigger | Action |
|---|---|
| {trigger} | {action} |

## Optional Personality Template
```yaml
personality:
  tone: {personality_tone}
  focus: {personality_focus}
```
"""

def init_org(path: Path):
    """Create a basic CorpAI folder structure and root roles."""
    roles_dir = path / "roles"
    spec_dir = path / "spec"
    
    roles_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Executive department
    exec_dir = roles_dir / "executive"
    exec_dir.mkdir(exist_ok=True)
    
    # Create OWNER role
    owner_content = "# [OWNER] Human Principal\n\n> The human overseer of the AI organization.\n\n## Identity\n- **Rank:** OWNER\n- **Department:** executive\n- **Reports to:** —\n- **Domain:** All"
    (exec_dir / "owner.md").write_text(owner_content, encoding="utf-8")
    
    # Create CEO role
    ceo_content = BASIC_ROLE_TEMPLATE.format(
        rank="L5",
        title="CEO",
        description="The executive head of the organization, responsible for high-level strategy and vision.",
        department="executive",
        reports_to="OWNER",
        domain="Organizational Strategy",
        responsibility="Set organizational goals and priorities.",
        comm_patterns="Sends tasks to L5 executives; receives escalations from the entire org.",
        trigger="Major budget deficit",
        action="Escalate to OWNER",
        personality_tone="Strategic, decisive, and visionary.",
        personality_focus="Mission alignment and cross-department coordination."
    )
    (exec_dir / "ceo.md").write_text(ceo_content, encoding="utf-8")
    
    # Create a README.md
    readme_content = "# My CorpAI Org\n\nThis is a [CorpAI](https://github.com/Arigitshub/CorpAI) organization.\n\n## Structure\n- `roles/`: Role definitions\n- `spec/`: Organization-specific protocols"
    (path / "README.md").write_text(readme_content, encoding="utf-8")
    
    return True


def create_role(roles_dir: Path, title: str, dept: str, rank: str) -> Path:
    """Create a single role file in a department directory."""
    dept_dir = roles_dir / dept.lower().replace(" ", "-")
    dept_dir.mkdir(exist_ok=True)
    
    filename = f"{title.lower().replace(' ', '-')}.md"
    file_path = dept_dir / filename
    
    if file_path.exists():
        raise FileExistsError(f"Role file already exists: {file_path}")
        
    content = BASIC_ROLE_TEMPLATE.format(
        rank=rank.upper(),
        title=title,
        description=f"Initial description for {title}.",
        department=dept.lower(),
        reports_to="{Role it reports to}",
        domain="{Area of responsibility}",
        responsibility="Execute primary objectives for this domain.",
        comm_patterns=f"Sends TASK to subordinates; receives ESCALATIONS.",
        trigger="Blocker in mission execution",
        action="Escalate to manager",
        personality_tone="Professional, efficient, and precise.",
        personality_focus=f"Success in {dept} operations."
    )
    
    file_path.write_text(content, encoding="utf-8")
    return file_path
