"""Progress reporting for long-running tnh-gen CLI operations."""
from __future__ import annotations

import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from rich.console import Console


@contextmanager
def run_progress(
    prompt_key: str,
    input_file: Path,
    *,
    quiet: bool = False,
    api: bool = False,
    no_color: bool = False,
) -> Iterator[None]:
    """Show a spinner and elapsed time on stderr while a prompt run is in flight.

    No-ops in --quiet and --api modes, and when stderr is not a TTY.
    """
    if quiet or api or not sys.stderr.isatty():
        yield
        return

    console = Console(stderr=True, highlight=False, no_color=no_color)
    label = f"[tnh-gen] {prompt_key} ← {input_file.name}"
    start = time.monotonic()
    stop_event = threading.Event()

    def _tick(status: object) -> None:
        while not stop_event.wait(timeout=1.0):
            elapsed = time.monotonic() - start
            m, s = divmod(int(elapsed), 60)
            status.update(f"{label}  [{m}:{s:02d}]")  # type: ignore[attr-defined]

    with console.status(f"{label}  [0:00]", spinner="dots") as status:
        thread = threading.Thread(target=_tick, args=(status,), daemon=True)
        thread.start()
        try:
            yield
        finally:
            stop_event.set()
            thread.join()
