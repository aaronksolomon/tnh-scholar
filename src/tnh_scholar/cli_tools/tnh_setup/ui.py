from dataclasses import dataclass
from typing import Callable, Iterable

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


@dataclass(frozen=True)
class SetupSummaryItem:
    component: str
    status: str
    style: str


@dataclass
class SetupUI:
    console: Console
    use_rich: bool

    @classmethod
    def create(cls) -> "SetupUI":
        console = Console()
        return cls(console=console, use_rich=console.is_terminal)

    def banner(self) -> None:
        if self.use_rich:
            self.console.print()
            self.console.print("[bold blue]TNH Scholar[/bold blue] [dim]- Setup Wizard[/dim]")
            self.console.print("[dim]" + "─" * 40 + "[/dim]")
        else:
            self.console.print("TNH Scholar — Setup Wizard")
            self.console.print("-" * 40)

    def section(self, step: int, title: str, total: int = 3) -> None:
        if self.use_rich:
            self.console.print()
            self.console.print(
                Panel(
                    f"[bold]{title}[/bold]",
                    title=f"[dim]Step {step}/{total}[/dim]",
                    border_style="blue",
                    width=60,
                )
            )
        else:
            self.console.print("")
            self.console.print(f"Step {step}/{total}: {title}")
            self.console.print("-" * 40)

    def status(self, label: str, status: str, style: str = "info") -> None:
        icon = self._icon(style)
        if self.use_rich:
            self.console.print(f"  {icon} [bold]{label}[/bold]: {status}")
        else:
            self.console.print(f"  {icon} {label}: {status}")

    def spinner(self, label: str, action: Callable[[], bool]) -> bool:
        if not self.use_rich:
            return action()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            progress.add_task(label, total=None)
            return action()

    def summary(self, items: Iterable[SetupSummaryItem]) -> None:
        if self.use_rich:
            table = Table(title="Setup Summary", show_header=False, box=None)
            table.add_column("Component", style="bold")
            table.add_column("Status")
            for item in items:
                table.add_row(item.component, self._colorize(item.status, item.style))
            self.console.print("")
            self.console.print(table)
            return

        self.console.print("")
        self.console.print("Setup Summary")
        self.console.print("-" * 20)
        for item in items:
            self.console.print(f"{item.component}: {item.status}")

    def _colorize(self, text: str, style: str) -> str:
        color = {
            "ok": "green",
            "warn": "yellow",
            "error": "red",
            "skip": "dim",
            "info": "blue",
        }.get(style, "white")
        return f"[{color}]{text}[/{color}]"

    def _icon(self, style: str) -> str:
        return {
            "ok": "[green][OK][/green]",
            "warn": "[yellow][WARN][/yellow]",
            "error": "[red][ERR][/red]",
            "skip": "[dim][SKIP][/dim]",
            "info": "[blue][INFO][/blue]",
        }.get(style, "")
