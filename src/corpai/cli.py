"""CorpAI CLI — corpai lint | corpai graph | corpai simulate"""

from __future__ import annotations
import sys
import io
from pathlib import Path
from typing import Optional

# Force UTF-8 on Windows so Rich can render unicode box chars
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.platform == "win32" and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.rule import Rule

app = typer.Typer(
    name="corpai",
    help="CorpAI CLI — validator and tooling for the CorpAI open standard.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)


def _resolve_roles_dir(path: Optional[Path]) -> Path:
    """Find the roles/ directory from a given path or cwd."""
    if path is None:
        path = Path.cwd()

    # If given path is a roles/ dir directly
    if path.is_dir() and path.name == "roles":
        return path

    # Look for roles/ subdirectory
    candidate = path / "roles"
    if candidate.is_dir():
        return candidate

    # Maybe it's already inside a roles tree
    if path.is_dir():
        return path

    typer.echo(f"[red]Could not find roles/ directory in {path}[/red]", err=True)
    raise typer.Exit(1)


# ─────────────────────────────────────────────────────────
# corpai lint
# ─────────────────────────────────────────────────────────

@app.command()
def lint(
    path: Optional[Path] = typer.Argument(None, help="Path to CorpAI repo or roles/ directory"),
    strict: bool = typer.Option(False, "--strict", "-s", help="Treat warnings as errors"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Lint a single role file"),
):
    """
    [bold]Validate role files against the CorpAI spec.[/bold]

    Checks for missing sections, invalid ranks, empty fields,
    broken reporting chains, and more.
    """
    from .validator import lint_role, lint_org

    if file:
        if not file.exists():
            err_console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(1)
        role, errors = lint_role(file)
        _print_lint_results([(file, errors)], strict)
        return

    roles_dir = _resolve_roles_dir(path)
    console.print(f"\n[dim]Scanning:[/dim] {roles_dir}\n")

    roles, errors = lint_org(roles_dir)

    # Group errors by file
    by_file: dict[Path, list] = {}
    for e in errors:
        by_file.setdefault(e.path, []).append(e)

    _print_lint_results(list(by_file.items()), strict)

    # Summary
    error_count = sum(1 for e in errors if e.level == "error")
    warn_count = sum(1 for e in errors if e.level == "warning")
    role_count = len(roles)

    console.print()
    console.print(Rule())
    if error_count == 0 and (warn_count == 0 or not strict):
        console.print(f"[bold green]✓ {role_count} roles checked — all good![/bold green]")
    else:
        status = "error" if error_count > 0 or strict else "warning"
        color = "red" if status == "error" else "yellow"
        console.print(
            f"[bold {color}]{role_count} roles checked — "
            f"{error_count} error(s), {warn_count} warning(s)[/bold {color}]"
        )
        if error_count > 0 or strict:
            raise typer.Exit(1)


def _print_lint_results(items: list[tuple[Path, list]], strict: bool) -> None:
    from .models import LintError
    for file_path, errors in items:
        if not errors:
            console.print(f"[green]✓[/green] {file_path.name}")
            continue

        has_errors = any(e.level == "error" for e in errors)
        has_warns = any(e.level == "warning" for e in errors)

        icon = "[red]✗[/red]" if has_errors else "[yellow]⚠[/yellow]"
        console.print(f"{icon} [bold]{file_path.name}[/bold]  [dim]{file_path}[/dim]")

        for e in errors:
            if e.level == "error":
                console.print(f"    [red]ERROR[/red]   {e.message}")
            else:
                console.print(f"    [yellow]WARN [/yellow]  {e.message}")


# ─────────────────────────────────────────────────────────
# corpai graph
# ─────────────────────────────────────────────────────────

@app.command()
def graph(
    path: Optional[Path] = typer.Argument(None, help="Path to CorpAI repo or roles/ directory"),
    department: Optional[str] = typer.Option(None, "--dept", "-d", help="Filter to a single department"),
    format: str = typer.Option("tree", "--format", "-f", help="Output format: tree | mermaid"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save output to file"),
):
    """
    [bold]Generate an org chart from your role files.[/bold]

    Outputs an ASCII tree or Mermaid diagram of your agent hierarchy.
    """
    from .graph import generate_ascii_tree, generate_mermaid

    roles_dir = _resolve_roles_dir(path)

    if format == "mermaid":
        result = generate_mermaid(roles_dir, department)
        if output:
            output.write_text(result, encoding="utf-8")
            console.print(f"[green]✓[/green] Mermaid chart saved to {output}")
        else:
            console.print(Panel(result, title="Mermaid Org Chart", border_style="blue"))
    else:
        result = generate_ascii_tree(roles_dir, department)
        title = f"CorpAI Org Chart" + (f" — {department}" if department else "")
        if output:
            output.write_text(result, encoding="utf-8")
            console.print(f"[green]✓[/green] Tree saved to {output}")
        else:
            console.print(Panel(result, title=title, border_style="blue"))


# ─────────────────────────────────────────────────────────
# corpai simulate
# ─────────────────────────────────────────────────────────

@app.command()
def simulate(
    path: Optional[Path] = typer.Argument(None, help="Path to CorpAI repo or roles/ directory"),
    from_role: str = typer.Option(..., "--from", "-f", help="Sending role (e.g. 'CEO')"),
    to_role: str = typer.Option(..., "--to", "-t", help="Receiving role (e.g. 'Engineer')"),
    subject: str = typer.Option("Execute assigned task", "--subject", "-s", help="Message subject"),
    priority: str = typer.Option("P3", "--priority", "-p", help="Priority: P1–P5"),
):
    """
    [bold]Simulate a message flowing through your hierarchy.[/bold]

    Shows every hop a TASK or ESCALATION makes from source to destination,
    following the CorpAI chain-of-command rules.
    """
    from .simulator import simulate_task
    from .models import MessageType

    roles_dir = _resolve_roles_dir(path)

    try:
        messages = simulate_task(
            roles_dir,
            from_role=from_role,
            to_role=to_role,
            subject=subject,
            priority=priority,
        )
    except ValueError as e:
        err_console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if not messages:
        console.print("[yellow]No message path found between those roles.[/yellow]")
        raise typer.Exit(1)

    msg_type = messages[0].msg_type
    type_color = "red" if msg_type == MessageType.ESCALATION else "cyan"
    type_label = msg_type.value
    direction = "^ UP" if msg_type == MessageType.ESCALATION else "v DOWN"

    console.print()
    console.print(Panel(
        f"[bold]Subject:[/bold] {subject}\n"
        f"[bold]Type:[/bold]    [{type_color}]{type_label} ({direction})[/{type_color}]\n"
        f"[bold]Priority:[/bold] [yellow]{messages[0].priority.name}[/yellow]\n"
        f"[bold]Hops:[/bold]    {len(messages)}",
        title=f"[bold]CorpAI Message Simulation[/bold]",
        border_style=type_color,
    ))
    console.print()

    for msg in messages:
        arrow = "[red]^ ESCALATION[/red]" if msg.msg_type == MessageType.ESCALATION else "[cyan]v TASK[/cyan]"
        console.print(
            f"  [bold]Step {msg.step}[/bold]  {msg.from_role}  {arrow}  [bold]{msg.to_role}[/bold]"
        )

    console.print()
    final = messages[-1]
    console.print(f"[green]✓ Message delivered to {final.to_role}[/green]")


# ─────────────────────────────────────────────────────────
# corpai info
# ─────────────────────────────────────────────────────────

@app.command()
def info(
    path: Optional[Path] = typer.Argument(None, help="Path to CorpAI repo or roles/ directory"),
):
    """
    [bold]Show a summary of your CorpAI org.[/bold]

    Lists all departments, role counts per rank, and org health.
    """
    from .parser import load_roles_from_dir
    from .models import RankLevel, RANK_NAMES

    roles_dir = _resolve_roles_dir(path)
    roles = load_roles_from_dir(roles_dir)

    if not roles:
        console.print("[yellow]No roles found.[/yellow]")
        raise typer.Exit(1)

    # By department
    by_dept: dict[str, list] = {}
    for role in roles:
        by_dept.setdefault(role.department, []).append(role)

    # By rank
    by_rank: dict[str, int] = {}
    for role in roles:
        rank_name = role.rank.name if role.rank else "Unknown"
        by_rank[rank_name] = by_rank.get(rank_name, 0) + 1

    table = Table(title="CorpAI Org Summary", box=box.ROUNDED, border_style="blue")
    table.add_column("Department", style="bold")
    table.add_column("Roles", justify="right")
    table.add_column("Rank Distribution")

    for dept, dept_roles in sorted(by_dept.items()):
        rank_counts = {}
        for r in dept_roles:
            rn = r.rank.name if r.rank else "?"
            rank_counts[rn] = rank_counts.get(rn, 0) + 1
        rank_str = "  ".join(f"[dim]{k}[/dim]×{v}" for k, v in sorted(rank_counts.items()))
        table.add_row(dept, str(len(dept_roles)), rank_str)

    console.print()
    console.print(table)
    console.print()
    console.print(f"[bold]Total roles:[/bold] {len(roles)}  |  [bold]Departments:[/bold] {len(by_dept)}")
    console.print()


# ─────────────────────────────────────────────────────────
# corpai version
# ─────────────────────────────────────────────────────────

@app.command()
def version():
    """Show the CorpAI CLI version."""
    from . import __version__
    console.print(f"corpai v{__version__}")


if __name__ == "__main__":
    app()
