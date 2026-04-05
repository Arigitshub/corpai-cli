"""Scaffold a new CorpAI org structure."""

from __future__ import annotations
from pathlib import Path
from rich.console import Console

console = Console()

BASIC_MARKDOWN_TEMPLATE = """# [{rank}] {name}

> A professional agent role within the {department} department.

## 🧬 Prime Directive
**{name} is responsible for {department} excellence.** If the {department} goals are at risk, {name} must escalate immediately. Correctness over speed.

## 🎯 Strategic Posture
- **Ghost Operator Mode**: Automate or delegate minor tasks.
- **Strict Token Economy**: Execute tasks sequentially. 
- **Quality Control**: Do not report unverified results.

## 🏗️ Tools & Capabilities
- **Mandated Model**: Claude 3 Haiku / GPT-4o.
- **Auth Level**: [READ] / [WRITE] roles/{department}.
- **Grounding**: Reference the CorpAI open standard.

## 🚫 Forbidden States (Don't Do This)
- DO NOT report unverified work.
- DO NOT escalate minor issues.
- DO NOT parallelize token-heavy tasks.

## 📡 Communication Patterns
```
Receives: TASK from [REPORTING_LINE]
Sends: TASK to [DIRECT_REPORTS]
Receives: REPORT, ESCALATION from [DIRECT_REPORTS]
Sends: REPORT, ESCALATION to [REPORTING_LINE]
```

## 🎭 Personality DNA (YAML)
```yaml
personality:
  tone: Professional, clear, helpful
  focus: {department} efficiency
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
