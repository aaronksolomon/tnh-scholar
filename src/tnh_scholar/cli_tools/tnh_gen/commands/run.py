from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import typer

from tnh_scholar.cli_tools.tnh_gen.config_loader import CLIConfig, load_config
from tnh_scholar.cli_tools.tnh_gen.errors import error_response
from tnh_scholar.cli_tools.tnh_gen.factory import ServiceFactory, ServiceOverrides
from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.output.provenance import write_output_file
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx
from tnh_scholar.exceptions import ConfigurationError, ValidationError
from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope, RenderRequest
from tnh_scholar.gen_ai_service.protocols import GenAIServiceProtocol
from tnh_scholar.prompt_system.domain.models import PromptMetadata

logger = logging.getLogger(__name__)

app = typer.Typer(help="Execute a prompt with variable substitution.", invoke_without_command=True)


# ---- CLI Option Definitions ----


class TnhGenCLIOptions:
    """Encapsulates all CLI option definitions for the run command."""

    PROMPT = typer.Option(..., "--prompt", help="Prompt key to execute.")
    INPUT_FILE = typer.Option(..., "--input-file", help="Input file containing user content.")
    VARS_FILE = typer.Option(None, "--vars", help="JSON file with variable definitions.")
    VAR = typer.Option([], "--var", help="Inline variable assignment (repeatable).")
    MODEL = typer.Option(None, "--model", help="Model override.")
    INTENT = typer.Option(None, "--intent", help="Intent hint for routing.")
    MAX_TOKENS = typer.Option(None, "--max-tokens", help="Maximum output tokens.")
    TEMPERATURE = typer.Option(None, "--temperature", help="Model temperature.")
    TOP_P = typer.Option(None, "--top-p", help="Top-p sampling (not yet supported).")
    OUTPUT_FILE = typer.Option(None, "--output-file", help="Write result text to file.")
    FORMAT = typer.Option(
        None, "--format", help="Output format: json (default) or text.", case_sensitive=False
    )
    NO_PROVENANCE = typer.Option(False, "--no-provenance", help="Omit provenance block in files.")
    STREAMING = typer.Option(False, "--streaming", help="Enable streaming output (not implemented).")


# ---- Data Models ----


@dataclass
class RunContext:
    """Encapsulates all context needed for prompt execution."""

    prompt_key: str
    config: CLIConfig
    config_meta: dict[str, Any]
    service: GenAIServiceProtocol
    metadata: PromptMetadata
    variables: dict[str, Any]
    correlation_id: str
    model_override: str | None
    intent: str | None
    output_format: OutputFormat
    output_file: Path | None
    include_provenance: bool


# ---- Variable Handling ----


def _read_input_text(path: Path) -> str:
    """Read input text file with error handling.

    Args:
        path: Path to the user-provided input text file.

    Returns:
        Contents of the input file decoded as UTF-8.

    Raises:
        ValueError: If the file cannot be read.
    """
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        raise ValueError(f"Unable to read input file {path}") from exc


def _load_vars_file(path: Path | None) -> dict[str, Any]:
    """Load variables from JSON file.

    Args:
        path: Optional path to a JSON file containing variables.

    Returns:
        Dictionary of variables keyed by string names. Returns empty dict if
        no file is provided.

    Raises:
        json.JSONDecodeError: If the file cannot be parsed as JSON.
        ValueError: If the parsed JSON is not an object.
    """
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise json.JSONDecodeError(
            f"Invalid JSON in vars file {path}", exc.doc, exc.pos
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("--vars file must contain a JSON object")
    return {str(k): v for k, v in payload.items()}


def _parse_inline_vars(inline_vars: list[str]) -> dict[str, str]:
    """Parse inline `--var` key=value arguments."""
    variables: dict[str, str] = {}
    for item in inline_vars:
        if "=" not in item:
            raise ValueError(f"--var must be in KEY=VALUE form, got: {item!r}")
        key, value = item.split("=", 1)
        variables[key] = value
    return variables


def _merge_variables(
    input_file: Path,
    vars_file: Path | None,
    inline_vars: list[str],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    """Merge variables with correct precedence: defaults → input → vars file → inline.

    Args:
        input_file: Path to the primary input text file.
        vars_file: Optional JSON file containing variable overrides.
        inline_vars: Inline `--var` assignments.
        defaults: Prompt-provided default variables.

    Returns:
        Combined variable dictionary ready for rendering.
    """
    merged = dict(defaults)
    merged["input_text"] = _read_input_text(input_file)
    merged |= _load_vars_file(vars_file)
    merged.update(_parse_inline_vars(inline_vars))
    return _normalize_variable_keys(merged)


def _normalize_variable_keys(values: dict[Any, Any] | None) -> dict[str, Any]:
    """Normalize variable keys to strings for downstream components."""
    if not values:
        return {}
    return {str(k): v for k, v in values.items()}


def _ensure_input_text_variable(metadata: PromptMetadata) -> PromptMetadata:
    """Permit auto-injected input_text for legacy prompts without metadata."""
    if "input_text" in metadata.required_variables or "input_text" in metadata.optional_variables:
        return metadata
    optional = list(metadata.optional_variables) + ["input_text"]
    return metadata.model_copy(update={"optional_variables": optional})


def _validate_required_variables(variables: dict[str, Any], metadata: PromptMetadata) -> None:
    """Validate that all required variables are present.

    Args:
        variables: Variable dictionary to check.
        metadata: Prompt metadata that defines required variables.

    Raises:
        ValueError: If any required variable is missing.
    """
    if missing := [var for var in metadata.required_variables if var not in variables]:
        suggestion = " ".join(f"--var {var}=<value>" for var in missing)
        raise ValueError(
            f"Missing required variables: {', '.join(missing)}. Add with: {suggestion}"
        )


# ---- Service Initialization ----


def _initialize_service(
    config: CLIConfig,
    factory: ServiceFactory,
    model: str | None,
    max_tokens: int | None,
    temperature: float | None,
) -> GenAIServiceProtocol:
    """Build GenAI service with config and overrides.

    Args:
        config: Effective CLI configuration.
        factory: Service factory for constructing GenAI services.
        model: Optional model override for this invocation.
        max_tokens: Optional max output tokens override.
        temperature: Optional temperature override.

    Returns:
        A configured GenAI service instance.
    """
    overrides = ServiceOverrides(model=model, max_tokens=max_tokens, temperature=temperature)
    return factory.create_genai_service(config, overrides)


def _prepare_run_context(
    prompt_key: str,
    input_file: Path,
    vars_file: Path | None,
    inline_vars: list[str],
    model: str | None,
    intent: str | None,
    max_tokens: int | None,
    temperature: float | None,
    output_file: Path | None,
    output_format: OutputFormat | None,
    no_provenance: bool,
    correlation_id: str,
) -> RunContext:
    """Prepare all context needed for prompt execution.

    Args:
        prompt_key: Prompt key to execute.
        input_file: Path to user input text.
        vars_file: Optional path to JSON variables file.
        inline_vars: Inline variable assignments from CLI.
        model: Optional model override.
        intent: Optional routing intent.
        max_tokens: Optional max output tokens override.
        temperature: Optional temperature override.
        output_file: Optional path to write rendered output.
        output_format: Preferred CLI output format for stdout.
        no_provenance: Whether to skip provenance header when writing files.
        correlation_id: Trace identifier for this invocation.

    Returns:
        RunContext populated with config, service, metadata, and variables.

    Raises:
        ConfigurationError: If service factory is not initialized.
        ValueError: If required variables are missing or inputs are invalid.
    """
    # Load configuration
    config, meta = load_config(ctx.config_path, overrides={"default_model": model})

    # Get service factory from context
    factory = ctx.service_factory
    if factory is None:
        raise ConfigurationError("Service factory not initialized")

    # Initialize service
    service = _initialize_service(config, factory, model, max_tokens, temperature)

    # Get prompt metadata
    metadata = _ensure_input_text_variable(service.catalog.introspect(prompt_key))

    # Merge variables with correct precedence
    variables = _merge_variables(
        input_file, vars_file, inline_vars, defaults=metadata.default_variables
    )

    # Validate required variables
    _validate_required_variables(variables, metadata)

    return RunContext(
        prompt_key=prompt_key,
        config=config,
        config_meta=meta,
        service=service,
        metadata=metadata,
        variables=variables,
        correlation_id=correlation_id,
        model_override=model,
        intent=intent,
        output_format=output_format or ctx.output_format,
        output_file=output_file,
        include_provenance=not no_provenance,
    )


def _build_success_payload(
    envelope: CompletionEnvelope,
    metadata: PromptMetadata,
    config_meta: dict[str, Any],
    correlation_id: str,
) -> dict[str, Any]:
    """Build success response payload for CLI output serialization.

    This is the canonical place where the CLI output payload is constructed.
    Returns an untyped dict intended exclusively for direct output stream
    consumption (JSON/YAML serialization to stdout). No business logic should
    operate on this dict.

    If this payload needs to be consumed by business logic, passed between
    services, or used outside immediate serialization, it MUST be converted
    to a typed Pydantic model per Object-Service architecture (ADR-OS01).

    All upstream business logic uses typed CompletionEnvelope domain model.

    Args:
        envelope: Completion envelope returned from the service.
        metadata: Prompt metadata used for the invocation.
        config_meta: Metadata describing configuration sources.
        correlation_id: Trace identifier for the CLI invocation.

    Returns:
        Untyped payload suitable for serialization to stdout.
    """
    result = envelope.result
    usage = result.usage if result else None

    payload = {
        "status": "succeeded",
        "result": {
            "text": result.text if result else "",
            "model": result.model if result else None,
            "provider": result.provider if result else None,
            "usage": (
                {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                }
                if usage
                else None
            ),
            "finish_reason": result.finish_reason if result else None,
        },
        "provenance": {
            "backend": envelope.provenance.provider,
            "model": envelope.provenance.model,
            "prompt_key": envelope.provenance.fingerprint.prompt_key,
            "prompt_fingerprint": envelope.provenance.fingerprint.prompt_content_hash,
            "prompt_version": metadata.version,
            "started_at": envelope.provenance.started_at.isoformat(),
            "completed_at": envelope.provenance.finished_at.isoformat(),
            "schema_version": envelope.provenance.fingerprint.schema_version,
        },
        "warnings": envelope.warnings,
        "prompt_warnings": getattr(metadata, "warnings", []),
        "policy_applied": envelope.policy_applied,
        "sources": config_meta["sources"],
        "correlation_id": correlation_id,
    }
    return payload


# ---- Error Handling ----


def _handle_error(exc: Exception, correlation_id: str) -> None:
    """Handle error and exit with appropriate code.

    Args:
        exc: The caught exception.
        correlation_id: Trace identifier for the current invocation.

    Raises:
        typer.Exit: Always raised with the mapped exit code.
    """
    if not isinstance(exc, (ValueError, KeyError, json.JSONDecodeError, ValidationError, ConfigurationError)):
        logger.exception(f"Unexpected error in run command [correlation_id={correlation_id}]")

    payload, exit_code = error_response(exc, correlation_id=correlation_id)
    typer.echo(render_output(payload, OutputFormat.json))
    raise typer.Exit(code=int(exit_code)) from exc


# ---- CLI Command ----


@app.callback()
def run_prompt(
    prompt: str = TnhGenCLIOptions.PROMPT,
    input_file: Path = TnhGenCLIOptions.INPUT_FILE,
    vars_file: Path | None = TnhGenCLIOptions.VARS_FILE,
    var: list[str] = TnhGenCLIOptions.VAR,
    model: str | None = TnhGenCLIOptions.MODEL,
    intent: str | None = TnhGenCLIOptions.INTENT,
    max_tokens: int | None = TnhGenCLIOptions.MAX_TOKENS,
    temperature: float | None = TnhGenCLIOptions.TEMPERATURE,
    top_p: float | None = TnhGenCLIOptions.TOP_P,
    output_file: Path | None = TnhGenCLIOptions.OUTPUT_FILE,
    format: OutputFormat | None = TnhGenCLIOptions.FORMAT,
    no_provenance: bool = TnhGenCLIOptions.NO_PROVENANCE,
    streaming: bool = TnhGenCLIOptions.STREAMING,
) -> None:
    """Execute a prompt with variable substitution and AI processing.

    Args:
        prompt: Key of the prompt to execute.
        input_file: File containing the main user input text.
        vars_file: Optional JSON file with additional variables.
        var: Inline variable assignments (`--var key=value`).
        model: Optional model override for this run.
        intent: Optional routing intent to pass to the service.
        max_tokens: Max output tokens override.
        temperature: Temperature override.
        top_p: Top-p sampling override (accepted but not applied).
        output_file: Optional file to write the rendered text to.
        format: Output format for stdout.
        no_provenance: Whether to omit provenance header in written files.
        streaming: Whether to request streaming (not yet implemented).
    """
    correlation_id = uuid4().hex

    try:
        # Validate unsupported options
        if streaming:
            raise ValueError("Streaming output is not implemented yet.")
        if top_p is not None:
            typer.echo("Warning: --top-p is accepted but not applied in this version.", err=True)

        # Prepare execution context
        context = _prepare_run_context(
            prompt_key=prompt,
            input_file=input_file,
            vars_file=vars_file,
            inline_vars=var,
            model=model,
            intent=intent,
            max_tokens=max_tokens,
            temperature=temperature,
            output_file=output_file,
            output_format=format,
            no_provenance=no_provenance,
            correlation_id=correlation_id,
        )

        # Execute prompt
        user_input = str(context.variables.get("input_text", ""))
        request = RenderRequest(
            instruction_key=context.prompt_key,
            user_input=user_input,
            variables=context.variables,
            intent=context.intent,
            model=context.model_override,
        )
        envelope = context.service.generate(request)

        # Build response payload
        payload = _build_success_payload(
            envelope=envelope,
            metadata=context.metadata,
            config_meta=context.config_meta,
            correlation_id=context.correlation_id,
        )

        # Handle output
        result_text = envelope.result.text if envelope.result else ""
        if context.output_file:
            write_output_file(
                context.output_file,
                result_text=result_text,
                envelope=envelope,
                correlation_id=context.correlation_id,
                prompt_version=context.metadata.version,
                include_provenance=context.include_provenance,
            )
            typer.echo(f"Wrote output to {context.output_file}", err=True)

        typer.echo(render_output(payload, context.output_format))

    except Exception as exc:
        _handle_error(exc, correlation_id)
