from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from types import SimpleNamespace

import pytest
import typer
import yaml
from typer.testing import CliRunner

from tnh_scholar.cli_tools.tnh_gen import factory as factory_module
from tnh_scholar.cli_tools.tnh_gen import tnh_gen
from tnh_scholar.cli_tools.tnh_gen.commands import config as config_module
from tnh_scholar.cli_tools.tnh_gen.commands import list as list_module
from tnh_scholar.cli_tools.tnh_gen.commands import run as run_module
from tnh_scholar.cli_tools.tnh_gen.config_loader import (
    CLIConfig,
    _load_json,
    load_config,
    load_config_overrides,
    persist_config_value,
)
from tnh_scholar.cli_tools.tnh_gen.errors import (
    ExitCode,
    error_response,
    map_exception,
    render_error,
)
from tnh_scholar.cli_tools.tnh_gen.output import formatter as formatter_module
from tnh_scholar.cli_tools.tnh_gen.output import human_formatter as human_module
from tnh_scholar.cli_tools.tnh_gen.output import policy as policy_module
from tnh_scholar.cli_tools.tnh_gen.output import provenance as provenance_module
from tnh_scholar.cli_tools.tnh_gen.state import ListOutputFormat, OutputFormat, ctx
from tnh_scholar.exceptions import ConfigurationError, ExternalServiceError, ValidationError
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    CompletionResult,
    Fingerprint,
    Provenance,
    Usage,
)
from tnh_scholar.gen_ai_service.models.errors import ProviderError
from tnh_scholar.prompt_system.domain.models import PromptMetadata

runner = CliRunner(mix_stderr=False)


@contextmanager
def _patched_ctx(**updates):
    original = {key: getattr(ctx, key) for key in updates}
    try:
        for key, value in updates.items():
            setattr(ctx, key, value)
        yield
    finally:
        for key, value in original.items():
            setattr(ctx, key, value)


def _prompt_metadata(**overrides) -> PromptMetadata:
    base = {
        "key": "daily",
        "name": "Daily Guidance",
        "version": "1.0.0",
        "description": "Daily guidance prompt for testing.",
        "task_type": "study-plan",
        "required_variables": [],
        "optional_variables": [],
        "default_variables": {},
        "tags": [],
    }
    base.update(overrides)
    return PromptMetadata(**base)


def _envelope_with_warnings() -> CompletionEnvelope:
    started = datetime.now()
    finished = started
    return CompletionEnvelope(
        result=CompletionResult(
            text="generated text",
            usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            model="gpt-4o",
            provider="openai",
            finish_reason="stop",
        ),
        provenance=Provenance(
            provider="openai",
            model="gpt-4o",
            started_at=started,
            finished_at=finished,
            attempt_count=1,
            fingerprint=Fingerprint(
                prompt_key="daily",
                prompt_name="Daily Guidance",
                prompt_base_path=".",
                prompt_content_hash="hash-prompt",
                variables_hash="hash-vars",
                user_string_hash="hash-input",
            ),
        ),
        policy_applied={"routing_reason": "test"},
        warnings=["envelope-warning"],
    )


def _write_prompt(tmp_path) -> str:
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("daily.md").write_text(
        (
            "---\n"
            "key: daily\n"
            "name: Daily Guidance\n"
            "version: 1.0.0\n"
            "description: Daily guidance prompt for testing.\n"
            "task_type: study-plan\n"
            "required_variables: []\n"
            "optional_variables: []\n"
            "default_variables: {}\n"
            "tags:\n"
            "  - guidance\n"
            "---\n"
            "# Daily Guidance\n"
        ),
        encoding="utf-8",
    )
    return str(prompt_dir)


def _write_legacy_prompt(tmp_path) -> str:
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("legacy.md").write_text(
        ("---\n# legacy prompt without metadata\n---\n# Legacy Prompt\n"),
        encoding="utf-8",
    )
    return str(prompt_dir)


def test_config_coerce_and_format_text():
    assert config_module._coerce_for_set("prompt_catalog_dir", "docs") == "docs"
    assert config_module._coerce_for_set("max_dollars", "1.5") == 1.5
    assert config_module._coerce_for_set("default_temperature", "0.7") == 0.7
    assert config_module._coerce_for_set("max_input_chars", "9") == 9

    assert config_module._format_config_text({}) == ""
    overrides = {"cli_path": ["one", "two"], "default_model": "gpt-4o"}
    rendered = config_module._format_config_text(overrides)
    assert "cli_path:" in rendered
    assert "default_model: gpt-4o" in rendered


def test_render_config_response_requires_api_payload():
    with _patched_ctx(api=True, output_format=OutputFormat.json):
        with pytest.raises(RuntimeError):
            config_module._render_config_response(api_payload=None, human_payload=None)


def test_render_config_response_text_fallback():
    with _patched_ctx(api=False, output_format=None):
        output = config_module._render_config_response(
            api_payload={"trace_id": "trace"},
            human_payload={"default_model": "gpt-4o"},
            text_fallback="default_model: gpt-4o",
            format_override=OutputFormat.text,
        )
    assert output == "default_model: gpt-4o"


def test_config_get_unknown_key_returns_error(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["--api", "config", "get", "nope"])

    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "Unknown config key" in payload["error"]


def test_config_set_unknown_key_returns_error(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["--api", "config", "set", "nope", "1"])

    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "Unknown config key" in payload["error"]


def test_config_list_outputs_keys(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["--api", "config", "list"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "keys" in payload
    assert "default_model" in payload["keys"]


def test_config_list_handles_exceptions(monkeypatch):
    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(config_module, "available_keys", _boom)
    with pytest.raises(typer.Exit):
        config_module.list_config_keys()


def test_cli_config_with_overrides_ignores_none():
    base = CLIConfig(default_model="base", max_input_chars=100)
    updated = base.with_overrides({"default_model": None, "max_input_chars": 200})
    assert updated.default_model == "base"
    assert updated.max_input_chars == 200


def test_load_config_tracks_sources(tmp_path, monkeypatch):
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    config_home.joinpath("tnh-gen.json").write_text(
        json.dumps({"default_model": "user-model"}, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(config_home))

    workspace_config = tmp_path / ".tnh-gen.json"
    workspace_config.write_text(json.dumps({"max_input_chars": 111}, indent=2), encoding="utf-8")

    override_path = tmp_path / "override.json"
    override_path.write_text(json.dumps({"default_temperature": 0.2}, indent=2), encoding="utf-8")

    config, meta = load_config(
        config_path=override_path,
        cwd=tmp_path,
        overrides={"default_model": "cli-model"},
    )

    assert config.default_model == "cli-model"
    assert config.max_input_chars == 111
    assert config.default_temperature == 0.2
    assert meta["sources"] == [
        "defaults+env",
        "user",
        "workspace",
        str(override_path),
        "cli-overrides",
    ]
    assert str(override_path) in meta["config_files"]


def test_load_config_overrides_collects_sources(tmp_path, monkeypatch):
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    config_home.joinpath("tnh-gen.json").write_text(
        json.dumps({"default_model": "user-model"}, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(config_home))

    workspace_config = tmp_path / ".tnh-gen.json"
    workspace_config.write_text(json.dumps({"max_input_chars": 111}, indent=2), encoding="utf-8")

    override_path = tmp_path / "override.json"
    override_path.write_text(json.dumps({"default_temperature": 0.2}, indent=2), encoding="utf-8")

    overrides = load_config_overrides(config_path=override_path, cwd=tmp_path)
    assert overrides["default_model"] == "user-model"
    assert overrides["max_input_chars"] == 111
    assert overrides["default_temperature"] == 0.2


def test_persist_config_value_rejects_unknown_key(tmp_path):
    with pytest.raises(KeyError):
        persist_config_value("nope", "value", cwd=tmp_path)


def test_load_json_rejects_invalid_payloads(tmp_path):
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError):
        _load_json(invalid_json)

    non_object = tmp_path / "list.json"
    non_object.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        _load_json(non_object)


def test_list_outputs_yaml_payload(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["list", "--format", "yaml"])

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.stdout)
    assert payload["count"] == 1
    assert payload["prompts"][0]["key"] == "daily"


def test_list_quiet_suppresses_warnings(tmp_path, monkeypatch):
    prompt_dir = _write_legacy_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["--quiet", "--api", "list"])

    assert result.exit_code == 0
    assert result.stderr == ""


def test_list_missing_prompt_dir_errors_as_json(tmp_path, monkeypatch):
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    config_home.joinpath("tnh-gen.json").write_text(
        json.dumps({"prompt_catalog_dir": None}, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(config_home))

    result = runner.invoke(tnh_gen.app, ["--api", "list", "--format", "json"])

    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "prompt catalog directory" in payload["error"].lower()


def test_list_missing_prompt_dir_errors_human(tmp_path, monkeypatch):
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    config_home.joinpath("tnh-gen.json").write_text(
        json.dumps({"prompt_catalog_dir": None}, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(config_home))

    result = runner.invoke(tnh_gen.app, ["list"])

    assert result.exit_code != 0
    assert "Error:" in result.stdout


def test_list_callback_reraises_typer_exit(monkeypatch):
    monkeypatch.setattr(list_module, "_list_prompts_impl", lambda **_: (_ for _ in ()).throw(typer.Exit()))
    with pytest.raises(typer.Exit):
        list_module.list_prompts()


def test_parse_inline_vars_requires_equals():
    with pytest.raises(ValueError):
        run_module._parse_inline_vars(["missing-equals"])


def test_ensure_input_text_variable_noop_when_present():
    metadata = _prompt_metadata(required_variables=["input_text"])
    assert run_module._ensure_input_text_variable(metadata) is metadata


def test_prepare_run_context_requires_factory(tmp_path, monkeypatch):
    input_file = tmp_path / "input.txt"
    input_file.write_text("file-input", encoding="utf-8")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    with _patched_ctx(service_factory=None):
        with pytest.raises(ConfigurationError):
            run_module._prepare_run_context(
                prompt_key="daily",
                input_file=input_file,
                vars_file=None,
                inline_vars=[],
                model=None,
                intent=None,
                max_tokens=None,
                temperature=None,
                output_file=None,
                output_format=None,
                no_provenance=False,
                trace_id="trace",
            )


def test_initialize_service_uses_factory_overrides():
    class _StubFactory:
        def __init__(self):
            self.overrides = None

        def create_genai_service(self, cli_config, overrides):  # noqa: ANN001, D401
            self.overrides = overrides
            return "service"

    factory = _StubFactory()
    config = CLIConfig()
    service = run_module._initialize_service(config, factory, model="gpt-4o", max_tokens=10, temperature=0.5)

    assert service == "service"
    assert factory.overrides.model == "gpt-4o"
    assert factory.overrides.max_tokens == 10
    assert factory.overrides.temperature == 0.5


def test_emit_warnings_respects_quiet(capsys):
    metadata = _prompt_metadata(warnings=["metadata-warning"])
    run_module._emit_warnings(_envelope_with_warnings(), metadata, quiet=True)
    captured = capsys.readouterr()
    assert captured.err == ""


def test_emit_warnings_outputs_to_stderr(capsys):
    metadata = _prompt_metadata(warnings=["metadata-warning"])
    run_module._emit_warnings(_envelope_with_warnings(), metadata, quiet=False)
    captured = capsys.readouterr()
    assert "[warn]" in captured.err


def test_validate_run_options_streaming_and_top_p(capsys):
    with pytest.raises(ValueError):
        run_module._validate_run_options(streaming=True, top_p=None)

    run_module._validate_run_options(streaming=False, top_p=0.5)
    captured = capsys.readouterr()
    assert "top-p" in captured.err.lower()


def test_output_formatters_cover_text_and_table_errors():
    payload = {"status": "ok"}
    rendered = formatter_module.render_output(payload, OutputFormat.text)
    assert rendered.startswith("{")

    with pytest.raises(ValueError):
        formatter_module.render_output(payload, ListOutputFormat.table)

    assert formatter_module.render_output("table", ListOutputFormat.table) == "table"
    with pytest.raises(ValueError):
        formatter_module.render_output(payload, "invalid-format")


def test_output_policy_paths():
    fmt_override = policy_module.resolve_output_format(
        api=False,
        format_override=OutputFormat.yaml,
        default_format=OutputFormat.text,
    )
    assert fmt_override == OutputFormat.yaml
    fmt = policy_module.resolve_output_format(api=True, format_override=None, default_format=OutputFormat.yaml)
    assert fmt == OutputFormat.json

    ctx_format = SimpleNamespace(value="invalid")
    list_fmt = policy_module.resolve_list_format(api=False, format_override=None, ctx_format=ctx_format)
    assert list_fmt == ListOutputFormat.text

    with pytest.raises(typer.BadParameter):
        policy_module.validate_global_format(api=True, format_override=OutputFormat.text)
    with pytest.raises(typer.BadParameter):
        policy_module.validate_global_format(api=False, format_override=OutputFormat.json)
    with pytest.raises(typer.BadParameter):
        policy_module.validate_list_format(api=True, format_override=ListOutputFormat.text)
    with pytest.raises(typer.BadParameter):
        policy_module.validate_list_format(api=False, format_override=ListOutputFormat.json)
    with pytest.raises(typer.BadParameter):
        policy_module.validate_run_format(api=True, format_override=OutputFormat.text)
    with pytest.raises(typer.BadParameter):
        policy_module.validate_run_format(api=False, format_override=OutputFormat.yaml)


def test_error_helpers_cover_suggestion_and_api_text_format():
    payload, code = error_response(ValueError("nope"), suggestion="try again", trace_id="trace")
    assert code == ExitCode.INPUT_ERROR
    assert payload["diagnostics"]["suggestion"] == "try again"

    assert map_exception(ValidationError("bad")) == ExitCode.POLICY_ERROR
    assert map_exception(ExternalServiceError("bad")) == ExitCode.TRANSPORT_ERROR
    assert map_exception(ProviderError("bad")) == ExitCode.PROVIDER_ERROR
    assert map_exception(RuntimeError("bad")) == ExitCode.PROVIDER_ERROR

    with _patched_ctx(api=True, output_format=OutputFormat.json):
        output, _, _ = render_error(ValueError("nope"), trace_id="trace", format_override=OutputFormat.text)
    decoded = json.loads(output)
    assert decoded["status"] == "failed"


def test_human_formatter_includes_empty_vars_and_suggestion():
    metadata = _prompt_metadata(required_variables=[], optional_variables=[])
    text = human_module.format_human_friendly_list([metadata])
    assert "(none)" in text

    error_text = human_module.format_human_friendly_error(ValueError("bad"), suggestion="fix it")
    assert "Suggestion:" in error_text


def test_provenance_write_without_header(tmp_path):
    output_file = tmp_path / "output.txt"
    envelope = _envelope_with_warnings()
    provenance_module.write_output_file(
        output_file,
        result_text="plain text",
        envelope=envelope,
        trace_id="trace",
        prompt_version=None,
        include_provenance=False,
    )
    assert output_file.read_text(encoding="utf-8") == "plain text"


def test_provenance_yaml_roundtrip(tmp_path):
    output_file = tmp_path / "output.txt"
    envelope = _envelope_with_warnings()
    provenance_module.write_output_file(
        output_file,
        result_text="plain text",
        envelope=envelope,
        trace_id="trace",
        prompt_version=None,
        include_provenance=True,
    )

    written = output_file.read_text(encoding="utf-8")
    header, body = written.split("---\n", 2)[1:]
    payload = yaml.safe_load(header)

    assert payload["tnh_scholar_generated"] is True
    assert payload["prompt_key"] == envelope.provenance.fingerprint.prompt_key
    assert payload["prompt_version"] == "unknown"
    assert payload["model"] == envelope.provenance.model
    assert payload["fingerprint"] == envelope.provenance.fingerprint.prompt_content_hash
    assert payload["trace_id"] == "trace"
    assert payload["generated_at"].endswith("Z")
    assert payload["schema_version"] == "1.0"
    assert body.lstrip("\n") == "plain text"


def test_main_dispatch_calls_app(monkeypatch):
    called = {"count": 0}

    def _fake_app():
        called["count"] += 1

    monkeypatch.setattr(tnh_gen, "app", _fake_app)
    tnh_gen.main()

    assert called["count"] == 1


def test_version_yaml_outputs_human_payload():
    result = runner.invoke(tnh_gen.app, ["version", "--format", "yaml"])

    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.stdout)
    assert payload["tnh_gen"]


def test_factory_payload_and_protocol_coverage(tmp_path):
    cli_config = CLIConfig(
        prompt_catalog_dir=tmp_path,
        api_key="key",
        default_model="model",
        max_dollars=0.5,
        max_input_chars=100,
    )
    overrides = factory_module.ServiceOverrides(model="override", max_tokens=9, temperature=0.1)
    payload = factory_module.cli_config_to_settings_kwargs(cli_config, overrides)

    assert payload["prompt_dir"] == tmp_path
    assert payload["openai_api_key"] == "key"
    assert payload["default_model"] == "override"
    assert payload["max_dollars"] == 0.5
    assert payload["max_input_chars"] == 100
    assert payload["default_temperature"] == 0.1
    assert payload["default_max_output_tokens"] == 9

    result = factory_module.ServiceFactory.create_genai_service(
        SimpleNamespace(),
        cli_config,
        overrides,
    )
    assert result is None


def test_default_service_factory_builds_service(monkeypatch):
    captured = {}

    class _FakeService:
        def __init__(self, settings):
            captured["settings"] = settings

    monkeypatch.setattr(factory_module, "GenAIService", _FakeService)
    factory = factory_module.DefaultServiceFactory()
    service = factory.create_genai_service(CLIConfig(default_model="gpt-4o"), factory_module.ServiceOverrides())

    assert isinstance(service, _FakeService)
    assert captured["settings"].default_model == "gpt-4o"
