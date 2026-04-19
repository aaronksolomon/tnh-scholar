from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import typer

from tnh_scholar.cli_tools.tnh_gen.config_loader import CLIConfig, load_config
from tnh_scholar.cli_tools.tnh_gen.errors import ExitCode, emit_trace_id, render_error
from tnh_scholar.cli_tools.tnh_gen.factory import ServiceFactory, ServiceOverrides
from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.output.human_formatter import format_human_friendly_error
from tnh_scholar.cli_tools.tnh_gen.output.policy import resolve_output_format, validate_run_format
from tnh_scholar.cli_tools.tnh_gen.output.provenance import write_output_file
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx
from tnh_scholar.cli_tools.tnh_gen.types import (
    ConfigData,
    ConfigMeta,
    PolicyApplied,
    RunAdapterDiagnosticsPayload,
    RunFailurePayload,
    RunOutcomePayload,
    RunProvenancePayload,
    RunResultPayload,
    RunUsagePayload,
    VariableMap,
)
from tnh_scholar.exceptions import ConfigurationError, ValidationError
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    CompletionFailure,
    CompletionOutcomeStatus,
    RenderRequest,
)
from tnh_scholar.gen_ai_service.models.errors import SafetyBlocked
from tnh_scholar.gen_ai_service.protocols import GenAIServiceProtocol
from tnh_scholar.metadata import Frontmatter, Metadata
from tnh_scholar.prompt_system.domain.models import PromptMetadata

logger = logging.getLogger(__name__)

app = typer.Typer(help="Execute a prompt with variable substitution.", invoke_without_command=True)


# ---- CLI Option Definitions ----


class TnhGenCLIOptions:
    """Encapsulates all CLI option definitions for the run command."""

    CONFIG = typer.Option(
        None,
        "--config",
        help="Path to config file that overrides user/workspace config.",
    )
    API = typer.Option(
        False,
        "--api",
        help="Machine-readable API contract output (JSON by default).",
    )
    PROMPT_DIR = typer.Option(
        None,
        "--prompt-dir",
        help="Override the prompt catalog directory for this invocation.",
    )
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
        None, "--format", help="Output format: json or yaml (API mode only).", case_sensitive=False
    )
    NO_PROVENANCE = typer.Option(False, "--no-provenance", help="Omit provenance block in files.")
    STREAMING = typer.Option(False, "--streaming", help="Enable streaming output (not implemented).")


# ---- Data Models ----


@dataclass
class RunContext:
    """Encapsulates all context needed for prompt execution."""

    prompt_key: str
    config: CLIConfig
    config_meta: ConfigMeta
    service: GenAIServiceProtocol
    metadata: PromptMetadata
    input_metadata: Metadata
    variables: VariableMap
    trace_id: str
    model_override: str | None
    intent: str | None
    output_format: OutputFormat | None
    output_file: Path | None
    include_provenance: bool


# ---- Variable Handling ----


def _load_vars_file(path: Path | None) -> VariableMap:
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


def _parse_inline_vars(inline_vars: list[str]) -> VariableMap:
    """Parse inline `--var` key=value arguments."""
    variables: VariableMap = {}
    for item in inline_vars:
        if "=" not in item:
            raise ValueError(f"--var must be in KEY=VALUE form, got: {item!r}")
        key, value = item.split("=", 1)
        variables[key] = value
    return variables


def _read_input_document(input_file: Path) -> tuple[Metadata, str]:
    """Read input document frontmatter and body text.

    Raises:
        ValueError: If the input file cannot be read.
    """
    try:
        return Frontmatter.extract_from_file(input_file)
    except Exception as exc:
        raise ValueError(f"Unable to read input file {input_file}") from exc


def _merge_variables(
    input_text: str,
    vars_file: Path | None,
    inline_vars: list[str],
    defaults: VariableMap,
) -> VariableMap:
    """Merge variables with correct precedence: defaults → input → vars file → inline.

    Args:
        input_text: Body text extracted from the primary input document.
        vars_file: Optional JSON file containing variable overrides.
        inline_vars: Inline `--var` assignments.
        defaults: Prompt-provided default variables.

    Returns:
        Combined variable dictionary ready for rendering.
    """
    merged: VariableMap = dict(defaults)
    merged["input_text"] = input_text
    merged |= _load_vars_file(vars_file)
    merged.update(_parse_inline_vars(inline_vars))
    return _normalize_variable_keys(merged)


def _normalize_variable_keys(values: VariableMap | None) -> VariableMap:
    """Normalize variable keys to strings for downstream components."""
    return {str(k): v for k, v in values.items()} if values else {}


def _ensure_input_text_variable(metadata: PromptMetadata) -> PromptMetadata:
    """Permit auto-injected input_text for legacy prompts without metadata."""
    if "input_text" in metadata.required_variables or "input_text" in metadata.optional_variables:
        return metadata
    optional = list(metadata.optional_variables) + ["input_text"]
    return metadata.model_copy(update={"optional_variables": optional})


def _validate_required_variables(variables: VariableMap, metadata: PromptMetadata) -> None:
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
    trace_id: str,
    prompt_dir: Path | None = None,
) -> RunContext:
    """Prepare all context needed for prompt execution.

    Args:
        prompt_key: Prompt key to execute.
        input_file: Path to user input text.
        vars_file: Optional path to JSON variables file.
        inline_vars: Inline variable assignments from CLI.
        prompt_dir: Optional prompt catalog directory override.
        model: Optional model override.
        intent: Optional routing intent.
        max_tokens: Optional max output tokens override.
        temperature: Optional temperature override.
        output_file: Optional path to write rendered output.
        output_format: Preferred CLI output format for stdout.
        no_provenance: Whether to skip provenance header when writing files.
        trace_id: Unique trace identifier for this invocation.

    Returns:
        RunContext populated with config, service, metadata, and variables.

    Raises:
        ConfigurationError: If service factory is not initialized.
        ValueError: If required variables are missing or inputs are invalid.
    """
    # Load configuration
    overrides: ConfigData = {"default_model": model}
    config, meta = load_config(ctx.config_path, overrides=overrides, prompt_dir=prompt_dir)

    # Get service factory from context
    factory = ctx.service_factory
    if factory is None:
        raise ConfigurationError("Service factory not initialized")

    # Initialize service
    service = _initialize_service(config, factory, model, max_tokens, temperature)

    # Get prompt metadata
    metadata = _ensure_input_text_variable(service.catalog.introspect(prompt_key))
    input_metadata, input_text = _read_input_document(input_file)

    # Merge variables with correct precedence
    variables = _merge_variables(
        input_text,
        vars_file,
        inline_vars,
        defaults=metadata.default_variables,
    )

    # Validate required variables
    _validate_required_variables(variables, metadata)

    return RunContext(
        prompt_key=prompt_key,
        config=config,
        config_meta=meta,
        service=service,
        metadata=metadata,
        input_metadata=input_metadata,
        variables=variables,
        trace_id=trace_id,
        model_override=model,
        intent=intent,
        output_format=output_format or ctx.output_format,
        output_file=output_file,
        include_provenance=not no_provenance,
    )


def _result_payload_from_envelope(envelope: CompletionEnvelope) -> RunResultPayload | None:
    """Build the result payload when a completion result is present."""
    result = envelope.result
    if result is None:
        return None

    usage_payload: RunUsagePayload | None = None
    if result.usage:
        usage_payload = {
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
        }

    return {
        "text": result.text,
        "model": result.model,
        "provider": result.provider,
        "usage": usage_payload,
        "finish_reason": result.finish_reason,
    }


def _provenance_payload(
    envelope: CompletionEnvelope,
    metadata: PromptMetadata,
) -> RunProvenancePayload:
    """Build the provenance payload for API serialization."""
    return {
        "backend": envelope.provenance.provider,
        "model": envelope.provenance.model,
        "prompt_key": envelope.provenance.fingerprint.prompt_key,
        "prompt_fingerprint": envelope.provenance.fingerprint.prompt_content_hash,
        "prompt_version": metadata.version,
        "started_at": envelope.provenance.started_at.isoformat(),
        "completed_at": envelope.provenance.finished_at.isoformat(),
        "schema_version": envelope.provenance.fingerprint.schema_version,
    }


def _failure_payload(failure: CompletionFailure) -> RunFailurePayload:
    """Convert a typed completion failure into an API payload."""
    diagnostics = failure.adapter_diagnostics
    adapter_diagnostics: RunAdapterDiagnosticsPayload | None = None
    if diagnostics is not None:
        adapter_diagnostics = {
            "content_source": diagnostics.content_source,
            "content_part_count": diagnostics.content_part_count,
            "raw_finish_reason": diagnostics.raw_finish_reason,
            "extraction_notes": diagnostics.extraction_notes,
        }

    return {
        "reason": failure.reason.value,
        "message": failure.message,
        "retryable": failure.retryable,
        "adapter_diagnostics": adapter_diagnostics,
    }


def _build_success_payload(
    envelope: CompletionEnvelope,
    metadata: PromptMetadata,
    config_meta: ConfigMeta,
    trace_id: str,
) -> RunOutcomePayload:
    """Build run response payload for CLI output serialization.

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
        trace_id: Unique trace identifier for the CLI invocation.

    Returns:
        Untyped payload suitable for serialization to stdout.
    """
    result_payload = _result_payload_from_envelope(envelope)
    provenance_payload = _provenance_payload(envelope, metadata)
    policy_applied: PolicyApplied = dict(envelope.policy_applied or {})
    prompt_warnings = list(getattr(metadata, "warnings", []) or [])
    warnings = list(envelope.warnings or [])
    sources = list(config_meta["sources"])

    base_payload = {
        "provenance": provenance_payload,
        "warnings": warnings,
        "prompt_warnings": prompt_warnings,
        "policy_applied": policy_applied,
        "sources": sources,
        "trace_id": trace_id,
    }

    match envelope.outcome:
        case CompletionOutcomeStatus.SUCCEEDED:
            if result_payload is None:
                raise ValueError("succeeded envelopes require result")
            return {
                **base_payload,
                "status": "succeeded",
                "result": result_payload,
            }
        case CompletionOutcomeStatus.INCOMPLETE:
            if result_payload is None:
                raise ValueError("incomplete envelopes require result")
            return {
                **base_payload,
                "status": "incomplete",
                "result": result_payload,
            }
        case CompletionOutcomeStatus.FAILED:
            if envelope.failure is None:
                raise ValueError("failed envelopes require failure")
            return {
                **base_payload,
                "status": "failed",
                "failure": _failure_payload(envelope.failure),
            }
    raise ValueError(f"Unsupported completion outcome: {envelope.outcome}")


# ---- Output Handling ----


def _emit_warnings(
    envelope: CompletionEnvelope,
    metadata: PromptMetadata | None = None,
    quiet: bool = False,
    api: bool = False,
) -> None:
    if quiet or api:
        return
    for warning in envelope.warnings or []:
        typer.echo(f"[warn] {warning}", err=True)


def _emit_catalog_health_summary(context: RunContext, api: bool) -> None:
    """Emit a single fatal catalog-health summary in human mode."""
    if api or ctx.quiet:
        return
    health_getter = getattr(context.service.catalog, "catalog_health", None)
    if not callable(health_getter):
        return
    catalog_health = health_getter()
    if catalog_health.error_count == 0:
        return
    typer.echo(
        f"[tnh-gen] {catalog_health.error_count} prompts failed to load. "
        "Run 'tnh-gen config show --catalog-health' for details.",
        err=True,
    )


def _emit_stdout(
    payload: RunOutcomePayload,
    result_text: str,
    output_format: OutputFormat | None,
    api: bool,
) -> None:
    if api:
        fmt = resolve_output_format(
            api=True,
            format_override=output_format,
            default_format=OutputFormat.json,
        )
        typer.echo(render_output(payload, fmt))
        return
    typer.echo(result_text)


def _emit_completion_failure(
    trace_id: str,
    envelope: CompletionEnvelope,
    payload: RunOutcomePayload,
    output_format: OutputFormat | None,
    api: bool,
) -> None:
    if api:
        fmt = resolve_output_format(
            api=True,
            format_override=output_format,
            default_format=OutputFormat.json,
        )
        typer.echo(render_output(payload, fmt))
        return

    failure_message = envelope.failure.message if envelope.failure else "Completion failed."
    error_code = (
        envelope.failure.reason.value.upper()
        if envelope.failure is not None
        else "COMPLETION_FAILED"
    )
    emit_trace_id(trace_id, error_code)
    typer.echo(format_human_friendly_error(RuntimeError(failure_message)))


def _budget_block_details(exc: SafetyBlocked) -> tuple[float, float] | None:
    """Extract structured budget-block details when present."""
    if exc.blocked_reason != "budget":
        return None
    if exc.estimated_cost is None or exc.max_dollars is None:
        return None
    return exc.estimated_cost, exc.max_dollars


def _emit_budget_block(
    trace_id: str,
    estimated_cost: float,
    max_dollars: float,
    output_format: OutputFormat | None,
    api: bool,
) -> None:
    """Render a budget-block response with actionable guidance."""
    if api:
        payload = {
            "status": "blocked",
            "blocked_reason": "budget",
            "estimated_cost": estimated_cost,
            "max_dollars": max_dollars,
            "trace_id": trace_id,
        }
        fmt = resolve_output_format(
            api=True,
            format_override=output_format,
            default_format=OutputFormat.json,
        )
        typer.echo(render_output(payload, fmt))
        return

    emit_trace_id(trace_id, "SAFETY_BUDGET_BLOCKED")
    error = RuntimeError(
        f"Budget blocked: estimated cost ${estimated_cost:.4f} exceeds budget ${max_dollars:.4f}."
    )
    suggestion = (
        "Raise max_dollars in config, for example:\n"
        "  tnh-gen config set --workspace max_dollars 0.10"
    )
    typer.echo(format_human_friendly_error(error, suggestion=suggestion))


def _emit_run_output(
    context: RunContext,
    envelope: CompletionEnvelope,
    payload: RunOutcomePayload,
    api: bool,
) -> None:
    _emit_warnings(envelope, context.metadata, ctx.quiet, api)
    _emit_catalog_health_summary(context, api)
    if envelope.outcome is CompletionOutcomeStatus.FAILED:
        _emit_completion_failure(
            context.trace_id,
            envelope,
            payload,
            context.output_format,
            api,
        )
        raise typer.Exit(code=int(ExitCode.PROVIDER_ERROR))

    result_text = envelope.result.text if envelope.result else ""
    if context.output_file:
        write_output_file(
            context.output_file,
            result_text=result_text,
            envelope=envelope,
            source_metadata=context.input_metadata,
            trace_id=context.trace_id,
            prompt_version=context.metadata.version,
            include_provenance=context.include_provenance,
        )
        if not api:
            typer.echo(f"Wrote output to {context.output_file}", err=True)
    _emit_stdout(payload, result_text, context.output_format, api)


def _execute_prompt(context: RunContext) -> tuple[CompletionEnvelope, RunOutcomePayload]:
    """Execute the prompt for the given context and build the success payload."""
    user_input = str(context.variables.get("input_text", ""))
    request = RenderRequest(
        instruction_key=context.prompt_key,
        user_input=user_input,
        variables=context.variables,
        intent=context.intent,
        model=context.model_override,
    )
    envelope = context.service.generate(request)
    payload = _build_success_payload(
        envelope=envelope,
        metadata=context.metadata,
        config_meta=context.config_meta,
        trace_id=context.trace_id,
    )
    return envelope, payload


def _validate_run_options(streaming: bool, top_p: float | None) -> None:
    if streaming:
        raise ValueError("Streaming output is not implemented yet.")
    if top_p is not None:
        typer.echo("Warning: --top-p is accepted but not applied in this version.", err=True)


def _apply_api_settings(format_override: OutputFormat | None) -> None:
    effective_format = format_override or ctx.output_format
    validate_run_format(ctx.api, effective_format)


# ---- Error Handling ----


def _handle_error(exc: Exception, trace_id: str, format_override: OutputFormat | None) -> None:
    """Handle error and exit with appropriate code.

    Args:
        exc: The caught exception.
        trace_id: Unique trace identifier for the current invocation.

    Raises:
        typer.Exit: Always raised with the mapped exit code.
    """
    if not isinstance(exc, (ValueError, KeyError, json.JSONDecodeError, ValidationError, ConfigurationError)):
        logger.exception(f"Unexpected error in run command [trace_id={trace_id}]")

    output, exit_code, error_code = render_error(
        exc,
        trace_id=trace_id,
        format_override=format_override,
    )
    emit_trace_id(trace_id, error_code)
    typer.echo(output)
    raise typer.Exit(code=int(exit_code)) from exc


# ---- CLI Command ----


@app.callback()
def run_prompt(
    config: Path | None = TnhGenCLIOptions.CONFIG,
    api: bool = TnhGenCLIOptions.API,
    prompt_dir: Path | None = TnhGenCLIOptions.PROMPT_DIR,
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
        config: Optional path to an explicit config file.
        api: Whether to emit machine-readable API contract output.
        prompt_dir: Optional prompt catalog directory override.
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
    trace_id = uuid4().hex

    try:
        if config is not None:
            ctx.config_path = config
        if api:
            ctx.api = True

        _validate_run_options(streaming, top_p)
        _apply_api_settings(format)

        # Prepare execution context
        context = _prepare_run_context(
            prompt_key=prompt,
            input_file=input_file,
            vars_file=vars_file,
            inline_vars=var,
            prompt_dir=prompt_dir,
            model=model,
            intent=intent,
            max_tokens=max_tokens,
            temperature=temperature,
            output_file=output_file,
            output_format=format,
            no_provenance=no_provenance,
            trace_id=trace_id,
        )

        # Execute prompt and build response payload
        envelope, payload = _execute_prompt(context)

        _emit_run_output(context, envelope, payload, ctx.api)

    except SafetyBlocked as exc:
        budget_details = _budget_block_details(exc)
        if budget_details is None:
            _handle_error(exc, trace_id, format)
            return
        estimated_cost, max_dollars = budget_details
        _emit_budget_block(trace_id, estimated_cost, max_dollars, format, ctx.api)
        raise typer.Exit(code=int(ExitCode.POLICY_ERROR))
    except typer.Exit:
        raise
    except Exception as exc:
        _handle_error(exc, trace_id, format)
