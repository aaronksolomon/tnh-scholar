from __future__ import annotations

import json
from pathlib import Path
from typing import List
from uuid import uuid4

import typer

from tnh_scholar.cli_tools.tnh_gen.config_loader import load_config
from tnh_scholar.cli_tools.tnh_gen.errors import error_response
from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.output.provenance import write_output_file
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx
from tnh_scholar.gen_ai_service.config.settings import Settings
from tnh_scholar.gen_ai_service.models.domain import RenderRequest
from tnh_scholar.gen_ai_service.service import GenAIService

app = typer.Typer(help="Execute a prompt with variable substitution.", invoke_without_command=True)


def _read_input_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Unable to read input file {path}") from exc


def _load_vars(path: Path | None) -> dict:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise json.JSONDecodeError(f"Invalid JSON in vars file {path}", exc.doc, exc.pos)
    if not isinstance(payload, dict):
        raise ValueError("--vars file must contain a JSON object")
    return {str(k): v for k, v in payload.items()}


def _parse_inline(vars_inline: List[str]) -> dict:
    variables: dict[str, str] = {}
    for item in vars_inline:
        if "=" not in item:
            raise ValueError("--var must be in KEY=VALUE form")
        key, value = item.split("=", 1)
        variables[key] = value
    return variables


def _merge_variables(input_file: Path, vars_file: Path | None, inline_vars: List[str]) -> dict:
    merged: dict[str, str] = {}
    merged["input_text"] = _read_input_text(input_file)
    merged.update(_load_vars(vars_file))
    merged.update(_parse_inline(inline_vars))
    return merged


def _build_service(config, *, max_tokens: int | None, temperature: float | None) -> GenAIService:
    overrides = {}
    if config.prompt_catalog_dir:
        overrides["prompt_dir"] = config.prompt_catalog_dir
    if config.api_key:
        overrides["openai_api_key"] = config.api_key
    if config.default_model:
        overrides["default_model"] = config.default_model
    if config.max_dollars is not None:
        overrides["max_dollars"] = config.max_dollars
    if config.max_input_chars is not None:
        overrides["max_input_chars"] = config.max_input_chars
    if temperature is not None:
        overrides["default_temperature"] = temperature
    if max_tokens is not None:
        overrides["default_max_output_tokens"] = max_tokens

    settings = Settings(_env_file=None, **overrides)
    return GenAIService(settings=settings)


@app.callback()
def run_prompt(
    prompt: str = typer.Option(..., "--prompt", help="Prompt key to execute."),
    input_file: Path = typer.Option(
        ...,
        "--input-file",
        path_type=Path,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Input file containing user content.",
    ),
    vars_file: Path | None = typer.Option(
        None,
        "--vars",
        path_type=Path,
        exists=True,
        dir_okay=False,
        readable=True,
        help="JSON file with variable definitions.",
    ),
    var: List[str] = typer.Option([], "--var", help="Inline variable assignment (repeatable)."),
    model: str | None = typer.Option(None, "--model", help="Model override."),
    intent: str | None = typer.Option(None, "--intent", help="Intent hint for routing."),
    max_tokens: int | None = typer.Option(None, "--max-tokens", help="Maximum output tokens."),
    temperature: float | None = typer.Option(None, "--temperature", help="Model temperature."),
    top_p: float | None = typer.Option(None, "--top-p", help="Top-p sampling (not yet supported)."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        path_type=Path,
        writable=True,
        help="Write result text to file.",
    ),
    format: OutputFormat | None = typer.Option(
        None,
        "--format",
        help="Output format: json (default) or text.",
        case_sensitive=False,
    ),
    no_provenance: bool = typer.Option(False, "--no-provenance", help="Omit provenance block in files."),
    streaming: bool = typer.Option(False, "--streaming", help="Enable streaming output (not implemented)."),
):
    correlation_id = uuid4().hex
    try:
        if streaming:
            raise ValueError("Streaming output is not implemented yet.")
        if top_p is not None:
            typer.echo("Warning: --top-p is accepted but not applied in this version.", err=True)

        config, meta = load_config(
            ctx.config_path,
            overrides={"default_model": model},
        )
        variables = _merge_variables(input_file, vars_file, var)
        user_input = str(variables.get("input_text", ""))

        service = _build_service(config, max_tokens=max_tokens, temperature=temperature)
        request = RenderRequest(
            instruction_key=prompt,
            user_input=user_input,
            variables=variables,
            intent=intent,
            model=model,
        )
        envelope = service.generate(request)
        prompt_metadata = None
        if hasattr(service, "catalog"):
            try:
                prompt_metadata = service.catalog.introspect(prompt)  # type: ignore[attr-defined]
            except Exception:
                prompt_metadata = None

        result = envelope.result
        usage = result.usage if result else None
        payload = {
            "status": "succeeded",
            "result": {
                "text": result.text if result else "",
                "model": result.model if result else None,
                "provider": result.provider if result else None,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens if usage else None,
                    "completion_tokens": usage.completion_tokens if usage else None,
                    "total_tokens": usage.total_tokens if usage else None,
                }
                if usage
                else None,
                "finish_reason": result.finish_reason if result else None,
            },
            "provenance": {
                "backend": envelope.provenance.provider,
                "model": envelope.provenance.model,
                "prompt_key": envelope.provenance.fingerprint.prompt_key,
                "prompt_fingerprint": envelope.provenance.fingerprint.prompt_content_hash,
                "prompt_version": prompt_metadata.version if prompt_metadata else None,
                "started_at": envelope.provenance.started_at.isoformat(),
                "completed_at": envelope.provenance.finished_at.isoformat(),
                "schema_version": envelope.provenance.fingerprint.schema_version,
            },
            "warnings": envelope.warnings,
            "prompt_warnings": prompt_metadata.warnings if prompt_metadata else [],
            "policy_applied": envelope.policy_applied,
            "sources": meta["sources"],
            "correlation_id": correlation_id,
        }

        fmt = format or ctx.output_format
        result_text = result.text if result else ""
        if output_file:
            write_output_file(
                output_file,
                result_text=result_text,
                envelope=envelope,
                correlation_id=correlation_id,
                prompt_version=prompt_metadata.version if prompt_metadata else None,
                include_provenance=not no_provenance,
            )
            typer.echo(f"Wrote output to {output_file}", err=True)

        typer.echo(render_output(payload, fmt))
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, OutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc
