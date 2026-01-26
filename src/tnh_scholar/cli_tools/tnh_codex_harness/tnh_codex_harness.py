"""Typer entrypoint for the Codex harness CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from tnh_scholar.agent_orchestration.codex_harness.adapters.output_parser import CodexOutputParser

from tnh_scholar.agent_orchestration.codex_harness.models import (
    CodexDefaults,
    CodexRunConfig,
    CodexRunParams,
    CodexSettings,
)
from tnh_scholar.agent_orchestration.codex_harness.providers.artifact_writer import FileArtifactWriter
from tnh_scholar.agent_orchestration.codex_harness.providers.chat_completions_client import (
    ChatCompletionsClient,
)
from tnh_scholar.agent_orchestration.codex_harness.providers.clock import SystemClock
from tnh_scholar.agent_orchestration.codex_harness.providers.openai_responses_client import OpenAIResponsesClient
from tnh_scholar.agent_orchestration.codex_harness.providers.patch_applier import GitPatchApplier
from tnh_scholar.agent_orchestration.codex_harness.providers.run_id import TimestampRunIdGenerator
from tnh_scholar.agent_orchestration.codex_harness.providers.searcher import RipgrepSearcher
from tnh_scholar.agent_orchestration.codex_harness.providers.tool_executor import CodexToolExecutor
from tnh_scholar.agent_orchestration.codex_harness.providers.tool_registry import CodexToolRegistry
from tnh_scholar.agent_orchestration.codex_harness.providers.test_runner import ShellTestRunner
from tnh_scholar.agent_orchestration.codex_harness.providers.workspace_locator import GitWorkspaceLocator
from tnh_scholar.agent_orchestration.codex_harness.service import CodexHarnessService
from tnh_scholar.agent_orchestration.codex_harness.tools import ToolSchemaFactory
from tnh_scholar.logging_config import get_logger, setup_logging

app = typer.Typer(
    name="tnh-codex-harness",
    help="Standalone Codex API harness.",
    add_completion=False,
    no_args_is_help=True,
)


@app.command("run")
def run_command(
    task: str = typer.Option(..., "--task", help="Task for Codex."),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", help="Optional system prompt."),
    apply_patch: bool = typer.Option(True, "--apply-patch/--no-apply-patch", help="Apply patch output."),
    run_tests_command: Optional[str] = typer.Option(
        None,
        "--run-tests",
        help="Test command to run after applying patch.",
    ),
    model: Optional[str] = typer.Option(None, "--model", help="Override the Codex model."),
    runs_root: Optional[str] = typer.Option(None, "--runs-root", help="Override runs root directory."),
    timeout_seconds: Optional[int] = typer.Option(None, "--timeout-seconds", help="Timeout for tests."),
    max_output_tokens: Optional[int] = typer.Option(None, "--max-output-tokens", help="Max output tokens."),
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature."),
    max_tool_rounds: Optional[int] = typer.Option(
        None,
        "--max-tool-rounds",
        help="Maximum tool-call rounds to allow.",
    ),
    use_chat_completions: bool = typer.Option(
        False,
        "--use-chat-completions",
        help="Use Chat Completions API instead of Responses API.",
    ),
) -> None:
    """Run a single Codex harness execution."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("codex-harness-start")
    settings = CodexSettings.from_env()
    defaults = CodexDefaults()
    resolved_runs_root = settings.runs_root if runs_root is None else Path(runs_root)
    resolved_model = settings.model if model is None else model
    config = CodexRunConfig(
        runs_root=resolved_runs_root,
        model=resolved_model,
    )
    resolved_timeout = defaults.timeout_seconds if timeout_seconds is None else timeout_seconds
    resolved_max_tokens = defaults.max_output_tokens if max_output_tokens is None else max_output_tokens
    resolved_temperature = temperature if temperature is not None else defaults.temperature
    resolved_tool_rounds = defaults.max_tool_rounds if max_tool_rounds is None else max_tool_rounds
    resolved_system_prompt = defaults.default_system_prompt if system_prompt is None else system_prompt
    params = CodexRunParams(
        task=task,
        system_prompt=resolved_system_prompt,
        apply_patch=apply_patch,
        run_tests_command=run_tests_command,
        timeout_seconds=resolved_timeout,
        max_output_tokens=resolved_max_tokens,
        temperature=resolved_temperature,
        max_tool_rounds=resolved_tool_rounds,
    )
    service = _build_service(settings, resolved_runs_root, use_chat_completions=use_chat_completions)
    metadata = service.run(params, config)
    logger.info("codex-harness-complete: %s", metadata.run_id)
    typer.echo(str(metadata.artifacts.run_metadata))


def _build_service(
    settings: CodexSettings,
    runs_root: Path,
    *,
    use_chat_completions: bool,
) -> CodexHarnessService:
    patch_applier = GitPatchApplier()
    test_runner = ShellTestRunner()
    tool_executor = CodexToolExecutor(
        workspace=GitWorkspaceLocator(),
        patch_applier=patch_applier,
        test_runner=test_runner,
        searcher=RipgrepSearcher(),
        test_timeout_seconds=CodexDefaults().timeout_seconds,
    )
    tool_registry = CodexToolRegistry(
        schema_factory=ToolSchemaFactory(),
        executor=tool_executor,
    )
    responses_client = (
        ChatCompletionsClient(api_key=settings.openai_api_key)
        if use_chat_completions
        else OpenAIResponsesClient(api_key=settings.openai_api_key)
    )
    return CodexHarnessService(
        clock=SystemClock(),
        run_id_generator=TimestampRunIdGenerator(),
        responses_client=responses_client,
        artifact_writer=FileArtifactWriter(runs_root=runs_root),
        output_parser=CodexOutputParser(),
        patch_applier=patch_applier,
        test_runner=test_runner,
        tool_registry=tool_registry,
    )


def main() -> None:
    """Dispatch to Typer app."""
    app()


if __name__ == "__main__":
    main()
