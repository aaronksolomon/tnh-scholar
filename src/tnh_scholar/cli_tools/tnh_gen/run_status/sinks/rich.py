"""Transient human presentation, isolated from orchestration."""

from rich.console import Console
from rich.status import Status
from rich.text import Text

from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunStatusEvent


class RichRunStatusSink:
    """Render status on stderr without interpreting user values as markup."""

    def __init__(self, *, no_color: bool = False) -> None:
        self._no_color = no_color
        self._status: Status | None = None

    def open(self) -> None:
        console = Console(stderr=True, highlight=False, no_color=self._no_color)
        self._status = console.status(Text("Preparing run"), spinner="dots")
        self._status.start()

    def emit(self, event: RunStatusEvent) -> None:
        if self._status is not None:
            minutes, seconds = divmod(event.elapsed_ms // 1000, 60)
            self._status.update(
                Text(
                    f"[tnh-gen] {event.metadata.prompt_key} ← {event.metadata.input_file_name} "
                    f"{event.message} [{minutes}:{seconds:02d}]"
                )
            )

    def close(self) -> None:
        status, self._status = self._status, None
        if status is not None:
            status.stop()
