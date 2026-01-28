"""Typer entrypoint for the tnh-conductor-spike CLI."""

from __future__ import annotations

from typing import Optional

import typer

from tnh_scholar.agent_orchestration.spike.adapters.command_filter import RegexCommandFilter
from tnh_scholar.agent_orchestration.spike.adapters.prompt_handler import RegexPromptHandler
from tnh_scholar.agent_orchestration.spike.adapters.prompt_parser import RegexCommandPromptParser
from tnh_scholar.agent_orchestration.spike.adapters.run_id import TimestampRunIdGenerator
from tnh_scholar.agent_orchestration.spike.models import (
    RunMetadata,
    SpikeConfig,
    SpikeDefaults,
    SpikeParams,
    SpikePolicy,
    SpikePreflightError,
    SpikeSettings,
)
from tnh_scholar.agent_orchestration.spike.policy import default_spike_policy
from tnh_scholar.agent_orchestration.spike.providers.artifact_writer import FileArtifactWriter
from tnh_scholar.agent_orchestration.spike.providers.clock import SystemClock
from tnh_scholar.agent_orchestration.spike.providers.command_builder import AgentCommandBuilder
from tnh_scholar.agent_orchestration.spike.providers.event_writer_factory import NdjsonEventWriterFactory
from tnh_scholar.agent_orchestration.spike.providers.git_workspace import GitWorkspaceCapture
from tnh_scholar.agent_orchestration.spike.providers.pty_agent_runner import PtyAgentRunner
from tnh_scholar.agent_orchestration.spike.service import SpikeRunService
from tnh_scholar.logging_config import get_logger, setup_logging

app = typer.Typer(
    name="tnh-conductor-spike",
    help="Phase 0 protocol layer spike runner.",
    add_completion=False,
    no_args_is_help=True,
)


@app.command("run")
def run_command(
    agent: str = typer.Option(..., "--agent", help="Agent identifier (claude-code, codex)."),
    task: Optional[str] = typer.Option(None, "--task", help="Task text for the agent."),
    prompt_id: Optional[str] = typer.Option(None, "--prompt-id", help="Prompt id for the task."),
    timeout_seconds: int = typer.Option(
        SpikeDefaults().default_timeout_seconds,
        "--timeout-seconds",
        help="Wall-clock timeout.",
    ),
    idle_timeout_seconds: int = typer.Option(
        SpikeDefaults().default_idle_timeout_seconds,
        "--idle-timeout-seconds",
        help="Idle timeout.",
    ),
    heartbeat_interval_seconds: int = typer.Option(
        SpikeDefaults().default_heartbeat_interval_seconds,
        "--heartbeat-interval-seconds",
        help="Heartbeat interval for progress events.",
    ),
    work_branch: Optional[str] = typer.Option(None, "--work-branch", help="Explicit work branch name."),
) -> None:
    """Run a single Phase 0 spike execution."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("spike-cli-start")
    settings = SpikeSettings.from_env()
    config = SpikeConfig(
        runs_root=settings.runs_root,
        work_branch_prefix=settings.work_branch_prefix,
        sandbox_root=settings.sandbox_root,
    )
    policy = default_spike_policy()
    service = _build_service(config, policy)
    params = SpikeParams(
        agent=agent,
        task=task,
        prompt_id=prompt_id,
        timeout_seconds=timeout_seconds,
        idle_timeout_seconds=idle_timeout_seconds,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        work_branch=work_branch,
    )
    try:
        metadata = service.run(params, config=config, policy=policy)
    except SpikePreflightError as exc:
        logger.error("spike-cli-preflight-failed: %s", exc)
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    logger.info("spike-cli-complete: %s", metadata.run_id)
    _print_outputs(metadata)


def _build_service(config: SpikeConfig, policy: SpikePolicy) -> SpikeRunService:
    command_filter = RegexCommandFilter(patterns=tuple(policy.blocked_command_patterns))
    parser = RegexCommandPromptParser(patterns=tuple(policy.command_capture_patterns))
    prompt_handler = RegexPromptHandler(
        parser=parser,
        command_filter=command_filter,
        interactive_patterns=tuple(policy.interactive_prompt_patterns),
        allow_response=policy.allow_response,
        block_response=policy.block_response,
    )
    return SpikeRunService(
        clock=SystemClock(),
        run_id_generator=TimestampRunIdGenerator(),
        agent_runner=PtyAgentRunner(),
        workspace=GitWorkspaceCapture(),
        artifact_writer=FileArtifactWriter(runs_root=config.runs_root),
        event_writer_factory=NdjsonEventWriterFactory(),
        command_builder=AgentCommandBuilder(),
        prompt_handler=prompt_handler,
    )


def _print_outputs(metadata: RunMetadata) -> None:
    artifacts = metadata.artifact_paths
    typer.echo(str(artifacts.transcript_normalized))
    typer.echo(str(artifacts.transcript_raw))
    typer.echo(str(artifacts.diff_patch))
    typer.echo(str(artifacts.run_metadata))
    typer.echo(str(artifacts.events))


def main() -> None:
    """Dispatch to the Typer app."""
    app()


if __name__ == "__main__":
    main()
