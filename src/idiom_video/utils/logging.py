from __future__ import annotations

from rich.console import Console


console = Console()


def info(message: str) -> None:
    console.print(message)


def warn(message: str) -> None:
    console.print(f"[yellow]Warning:[/yellow] {message}")
