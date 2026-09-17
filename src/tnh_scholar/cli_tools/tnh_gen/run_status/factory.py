"""Compose sinks at the CLI boundary."""

import typer

from tnh_scholar.cli_tools.tnh_gen.run_status.emitter import RunStatusEmitter
from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunStatusMetadata
from tnh_scholar.cli_tools.tnh_gen.run_status.policy import RunStatusConfig
from tnh_scholar.cli_tools.tnh_gen.run_status.sink import ManagedSink
from tnh_scholar.cli_tools.tnh_gen.run_status.sinks.jsonl import JsonlRunStatusSink
from tnh_scholar.cli_tools.tnh_gen.run_status.sinks.noop import NoOpRunStatusSink
from tnh_scholar.cli_tools.tnh_gen.run_status.sinks.rich import RichRunStatusSink


def _diagnostic(message: str) -> None:
    typer.echo(message, err=True)


def create_emitter(metadata: RunStatusMetadata, config: RunStatusConfig) -> RunStatusEmitter:
    """Keep required file initialization ahead of transient presentation."""
    sinks: list[ManagedSink] = []
    if config.status_file is not None:
        sinks.append(ManagedSink(JsonlRunStatusSink(config.status_file), _diagnostic, required=True))
    if config.interactive:
        sinks.append(ManagedSink(RichRunStatusSink(no_color=config.no_color), _diagnostic, transient=True))
    if not sinks:
        sinks.append(ManagedSink(NoOpRunStatusSink(), _diagnostic))
    return RunStatusEmitter(metadata, config, sinks)
