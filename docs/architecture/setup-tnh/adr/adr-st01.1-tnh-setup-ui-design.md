---
title: "ADR-ST01.1: tnh-setup UI Design"
description: "Design proposal for a polished, stylized CLI experience for tnh-setup."
type: "design-detail"
owner: "aaronksolomon"
author: "Claude Opus 4.5"
status: proposed
created: "2026-02-03"
parent_adr: "adr-st01-tnh-setup-runtime-hardening.md"
---

# ADR-ST01.1: tnh-setup UI Design

Design proposal for improving the visual presentation and user experience of the `tnh-setup` CLI command using Rich for styled terminal output.

- **Status**: Proposed
- **Date**: 2026-02-03
- **Owner**: aaronksolomon
- **Authors**: Claude Opus 4.5
- **Parent ADR**: [ADR-ST01: tnh-setup Runtime Hardening](/architecture/setup-tnh/adr/adr-st01-tnh-setup-runtime-hardening.md)

## Context

The current `tnh-setup` implementation (Typer version) uses basic `typer.echo()` calls with manually constructed section headers (`=====` lines) and ad-hoc status formatting. While functional, the output lacks visual hierarchy, consistent styling, and the polish expected from a modern CLI tool.

Goals for the UI redesign:

- Clear visual grouping of setup phases
- Consistent status indicators with color coding
- Progress feedback for long-running operations
- Summary view of setup results
- Maintain compatibility with `--no-input` and piped output scenarios

## Decision

### 1. Adopt Rich for terminal output

Use the [Rich](https://rich.readthedocs.io/) library for styled console output. Rich integrates well with Typer and provides panels, tables, spinners, and color support.

```python
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()
```

### 2. Section headers with panels

Replace `=====` dividers with Rich panels showing step progress:

```python
def _section_header(step: int, title: str, total: int = 3) -> None:
    console.print()
    console.print(Panel(
        f"[bold]{title}[/bold]",
        title=f"[dim]Step {step}/{total}[/dim]",
        border_style="blue",
        width=60,
    ))
```

### 3. Standardized status indicators

Define a consistent status vocabulary with color-coded icons:

| Style   | Icon | Color  | Usage                          |
|---------|------|--------|--------------------------------|
| `ok`    | `✓`  | green  | Successful check or action     |
| `warn`  | `⚠`  | yellow | Non-fatal issue or incomplete  |
| `error` | `✗`  | red    | Fatal error                    |
| `skip`  | `○`  | dim    | Skipped by user or flag        |
| `info`  | `•`  | blue   | Informational status           |

```python
def _status(label: str, status: str, style: str = "info") -> None:
    icons = {
        "ok": "[green]✓[/green]",
        "warn": "[yellow]⚠[/yellow]",
        "error": "[red]✗[/red]",
        "skip": "[dim]○[/dim]",
        "info": "[blue]•[/blue]",
    }
    icon = icons.get(style, "")
    console.print(f"  {icon} [bold]{label}[/bold]: {status}")
```

### 4. Spinners for async operations

Use transient spinners for network requests and subprocess calls:

```python
def _download_prompts_with_progress(config: SetupConfig) -> bool:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Downloading prompts...", total=None)
        return _download_prompts(config)
```

### 5. Summary table at completion

Display a final summary table showing the status of each component:

```python
def _print_summary(results: dict[str, str]) -> None:
    table = Table(title="Setup Summary", show_header=False, box=None)
    table.add_column("Component", style="bold")
    table.add_column("Status")

    for component, status in results.items():
        if "verified" in status or "complete" in status:
            color = "green"
        elif "skip" in status:
            color = "yellow"
        else:
            color = "red"
        table.add_row(component, f"[{color}]{status}[/{color}]")

    console.print()
    console.print(table)
```

### 6. Banner header

Add a clean banner at startup:

```python
def _print_banner() -> None:
    console.print()
    console.print("[bold blue]TNH Scholar[/bold blue] [dim]— Setup Wizard[/dim]")
    console.print("[dim]─" * 40 + "[/dim]")
```

### 7. Example output

```
TNH Scholar — Setup Wizard
────────────────────────────────────────

╭──────────────────── Step 1/3 ────────────────────╮
│                 API Key Check                     │
╰──────────────────────────────────────────────────╯
  ✓ OPENAI_API_KEY: configured

╭──────────────────── Step 2/3 ────────────────────╮
│              Prompt Directory                     │
╰──────────────────────────────────────────────────╯
  ✓ Config directory: ~/.config/tnh-scholar
  • Downloading prompts...
  ✓ Prompts installed: 12 files

╭──────────────────── Step 3/3 ────────────────────╮
│           YouTube Download Support                │
╰──────────────────────────────────────────────────╯
  ✓ JS runtime: deno (/opt/homebrew/bin/deno)
  ✓ curl_cffi: installed (pipx)
  ✓ yt-dlp config: ~/.config/yt-dlp/config

Setup Summary
─────────────
API Key        verified
Prompts        installed
yt-dlp runtime verified

✓ Setup complete
```

## Consequences

**Positive**

- Clear visual hierarchy guides users through multi-step setup
- Color-coded status indicators provide at-a-glance feedback
- Spinners give feedback during network/subprocess operations
- Summary table provides confirmation of what was configured
- Consistent styling across all tnh-scholar CLI tools (future)

**Negative**

- Adds Rich as a dependency (already commonly used with Typer)
- Rich output may not render correctly in all terminal emulators
- Need to handle `--no-input` / piped output gracefully (Rich auto-detects)

## Alternatives Considered

- **Keep typer.echo() with manual formatting**: Rejected due to inconsistent styling and lack of progress feedback.
- **Use click.style() directly**: Rejected; Rich provides more features (panels, tables, spinners) with less code.
- **Create custom ANSI escape sequences**: Rejected; reinventing what Rich already provides.

## Open Questions

*Resolved during review — see decisions below.*

### Q1: Should we extract a shared `tnh_cli_ui` module?

**Decision**: Yes, add as future research task. A shared module would enable consistent styling across all tnh-scholar CLI tools (tnh-gen, ytt-fetch, audio-transcribe, etc.). Added to project TODO as P3 exploration.

### Q2: Should spinners be disabled in `--verify-only` mode?

**Decision**: Defer. The `--verify-only` mode should already be fast since it skips actual setup operations. If performance becomes an issue, revisit. Not needed for initial implementation.

### Q3: Should we add a `--plain` flag to disable Rich formatting?

**Decision**: Not required for v1. Rich auto-detects terminal capabilities via `Console.is_terminal` and strips formatting when output is piped to files. Additionally:

- `TTY_COMPATIBLE=0` environment variable forces plain output
- `force_terminal=False` can be passed to `Console()` constructor

If users report edge cases where auto-detection fails, we can add `--plain` later. Document the environment variable workaround in CLI help.

**Reference**: [Rich Console API](https://rich.readthedocs.io/en/latest/console.html) documents `is_terminal`, `force_terminal`, and `TTY_COMPATIBLE` / `TTY_INTERACTIVE` environment variables.

---

## As-Built Notes & Addendums

*None.*
