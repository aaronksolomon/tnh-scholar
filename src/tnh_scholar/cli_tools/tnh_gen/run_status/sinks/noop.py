"""Silent runtime sink."""

from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunStatusEvent


class NoOpRunStatusSink:
    """Discard status when no consumer was requested."""

    def open(self) -> None:
        pass

    def emit(self, event: RunStatusEvent) -> None:
        pass

    def close(self) -> None:
        pass
