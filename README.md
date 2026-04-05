# corpai-cli

![CorpAI Hero](assets/hero.png)

> The official CLI for the [CorpAI open standard](https://github.com/Arigitshub/CorpAI) — validate, visualize, and simulate your AI agent org.

[![PyPI version](https://img.shields.io/pypi/v/corpai?style=flat-square)](https://pypi.org/project/corpai/)
[![Website](https://img.shields.io/badge/Portal-VOS--Live-blue?style=flat-square)](https://corpai-standard-vos.surge.sh)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue?style=flat-square)](https://pypi.org/project/corpai/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![CorpAI Compatible](https://img.shields.io/badge/CorpAI-Compatible-0a0a0a?style=flat-square)](https://github.com/Arigitshub/CorpAI)

---

## Install

```bash
pip install corpai
```

---

## Commands

### `corpai lint` — Validate your role files

Checks every role `.md` file against the CorpAI spec:
- Missing required sections
- Invalid or missing rank badges
- Empty fields and template placeholders
- Broken reporting chains (reports-to role doesn't exist)
- Missing escalation triggers

```bash
# Lint entire org
corpai lint

# Lint a specific directory
corpai lint ./my-corpai-org

# Lint a single file
corpai lint --file roles/executive/ceo.md

# Treat warnings as errors (strict mode)
corpai lint --strict
```

Example output:
```
✓ ceo.md
✓ cto.md
⚠ engineer.md
    WARN   No optional personality template found
✗ custom-role.md
    ERROR  Missing required section: ## Escalation Triggers
    ERROR  "Reports to" field is empty

──────────────────────────────
42 roles checked — 1 error(s), 3 warning(s)
```

---

### `corpai graph` — Generate org charts

Visualize your agent hierarchy as an ASCII tree or Mermaid diagram.

```bash
# ASCII tree (default)
corpai graph

# Mermaid diagram
corpai graph --format mermaid

# Filter to one department
corpai graph --dept engineering

# Save to file
corpai graph --format mermaid --output org.mmd
```

Example ASCII output:
```
└── [OWNER] OWNER  (executive)
    └── [L5] CEO  (executive)
        ├── [L5] CFO  (executive)
        │   └── [L4] Finance Director  (finance)
        │       ├── [L2] Financial Analyst  (finance)
        │       └── [L2] Auditor  (finance)
        └── [L5] CTO  (executive)
            └── [L4] Engineering Director  (engineering)
                └── [L3] Engineering Team Lead  (engineering)
```

---

### `corpai simulate` — Simulate message flows

Trace exactly how a TASK or ESCALATION travels through your hierarchy.

```bash
# Simulate a task flowing from CEO to Engineer
corpai simulate --from CEO --to Engineer --subject "Build auth module" --priority P2

# Simulate an escalation from L1 up to CEO
corpai simulate --from "Support Agent" --to CEO --priority P1
```

Example output:
```
╭─ CorpAI Message Simulation ───────────────────────╮
│ Subject:  Build auth module                        │
│ Type:     ↓ TASK                                   │
│ Priority: P2                                       │
│ Hops:     4                                        │
╰────────────────────────────────────────────────────╯

  Step 1  [L5] CEO  ↓ TASK  [L5] CTO
  Step 2  [L5] CTO  ↓ TASK  [L4] Engineering Director
  Step 3  [L4] Engineering Director  ↓ TASK  [L3] Engineering Team Lead
  Step 4  [L3] Engineering Team Lead  ↓ TASK  [L1] Engineer

✓ Message delivered to [L1] Engineer
```

---

### `corpai info` — Org summary

```bash
corpai info
```

Shows role counts, departments, and rank distribution across your org.

---

## Usage with CorpAI spec repo

```bash
git clone https://github.com/Arigitshub/CorpAI
cd CorpAI
pip install corpai

# Validate the full spec
corpai lint

# View the org
corpai graph

# Simulate a task
corpai simulate --from CEO --to "QA Tester" --subject "Test the release"
```

---

## Contributing

Issues and PRs welcome at [Arigitshub/corpai-cli](https://github.com/Arigitshub/corpai-cli).
