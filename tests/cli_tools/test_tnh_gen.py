from __future__ import annotations

import json
from datetime import datetime, timedelta
from textwrap import dedent
from typing import Any

from typer.testing import CliRunner

from tnh_scholar.cli_tools.tnh_gen import tnh_gen
from tnh_scholar.cli_tools.tnh_gen.commands import run as run_module
from tnh_scholar.cli_tools.tnh_gen.errors import ExitCode
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    CompletionResult,
    Fingerprint,
    Provenance,
    Usage,
)
from tnh_scholar.prompt_system.domain.models import PromptMetadata

runner = CliRunner(mix_stderr=False)


def _write_prompt(tmp_path) -> str:
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("daily.md").write_text(
        dedent(
            """\
            ---
            key: daily
            name: Daily Guidance
            version: 1.0.0
            description: Daily guidance prompt for testing.
            task_type: study-plan
            required_variables:
              - audience
            optional_variables:
              - location
            default_variables:
              location: Plum Village
            tags:
              - guidance
              - study
            ---
            # Daily Guidance
            
            Offer help to {{ audience }} at {{ location }}.
            """
        ),
        encoding="utf-8",
    )
    return str(prompt_dir)


def _write_legacy_prompt(tmp_path) -> str:
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("legacy.md").write_text(
        dedent(
            """\
            ---
            # legacy prompt without metadata
            ---
            # Legacy Prompt

            Translate the text: {{ input_text }}
            """
        ),
        encoding="utf-8",
    )
    return str(prompt_dir)


def _write_prompt_catalog(tmp_path) -> str:
    """Create a small catalog with multiple prompts for list filtering."""
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("daily.md").write_text(
        dedent(
            """\
            ---
            key: daily
            name: Daily Guidance
            version: 1.0.0
            description: Daily guidance prompt for testing.
            task_type: study-plan
            required_variables: []
            optional_variables: []
            default_variables: {}
            tags:
              - guidance
              - study
            default_model: gpt-4o
            ---
            # Daily Guidance
            
            Offer help.
            """
        ),
        encoding="utf-8",
    )
    prompt_dir.joinpath("zen.md").write_text(
        dedent(
            """\
            ---
            key: zen
            name: Zen Reflection
            version: 1.0.0
            description: Reflect on Zen teachings.
            task_type: reflection
            required_variables: []
            optional_variables: []
            default_variables: {}
            tags:
              - zen
              - reflection
            default_model: gpt-4o-mini
            ---
            # Zen Reflection
            
            Share a short reflection.
            """
        ),
        encoding="utf-8",
    )
    prompt_dir.joinpath("study.md").write_text(
        dedent(
            """\
            ---
            key: study
            name: Study Planner
            version: 1.0.0
            description: Plan a study session.
            task_type: planning
            required_variables: []
            optional_variables: []
            default_variables: {}
            tags:
              - study
              - planning
            default_model: gpt-4o
            ---
            # Study Planner
            
            Build a plan.
            """
        ),
        encoding="utf-8",
    )
    return str(prompt_dir)


def test_list_prompts_outputs_json(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["list", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["count"] == 1
    assert payload["prompts"][0]["key"] == "daily"
    assert payload["prompts"][0]["tags"] == ["guidance", "study"]


def test_list_keys_only(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["list", "--keys-only"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "daily"


def test_list_includes_warning_for_legacy_prompt(tmp_path, monkeypatch):
    prompt_dir = _write_legacy_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["list", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["count"] == 1
    warnings = payload["prompts"][0]["warnings"]
    assert warnings, "Expected warning for legacy prompt with missing metadata"
    assert "Expected YAML frontmatter keys" in warnings[0]
    assert "invalid-metadata" in payload["prompts"][0]["tags"]


def test_list_prompts_filters_by_tag_and_search(tmp_path, monkeypatch):
    prompt_dir = _write_prompt_catalog(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(
        tnh_gen.app,
        ["list", "--tag", "study", "--search", "Planner", "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    keys = [entry["key"] for entry in payload["prompts"]]
    assert keys == ["study"]


def test_list_prompts_table_output(tmp_path, monkeypatch):
    prompt_dir = _write_prompt_catalog(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["list", "--format", "table"])

    assert result.exit_code == 0, result.output
    lines = result.stdout.strip().splitlines()
    assert lines
    header = lines[0].split()
    assert header == ["KEY", "NAME", "TAGS", "MODEL"]
    keys = {line.split()[0] for line in lines[1:]}
    assert {"daily", "zen", "study"}.issubset(keys)
    assert all(len(line.split()) >= 4 for line in lines)


class _StubCatalog:
    def __init__(self, metadata: PromptMetadata):
        self._metadata = metadata

    def introspect(self, key: str) -> PromptMetadata:  # noqa: ARG002
        return self._metadata


class _StubService:
    def __init__(self, metadata: PromptMetadata):
        self.last_request: Any = None
        self.catalog = _StubCatalog(metadata)
        self._metadata = metadata

    def generate(self, request):
        self.last_request = request
        started = datetime.now()
        finished = started + timedelta(seconds=1)
        envelope = CompletionEnvelope(
            result=CompletionResult(
                text="generated text",
                usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
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
            warnings=[],
        )
        return envelope


class _CatalogBackedStubService:
    """Stub service that uses a real catalog for metadata warnings."""

    def __init__(self, prompt_dir: str):
        self.last_request: Any = None
        self.catalog = PromptsAdapter(prompts_base=prompt_dir)

    def generate(self, request):
        self.last_request = request
        metadata = self.catalog.introspect(request.instruction_key)
        started = datetime.now()
        finished = started + timedelta(seconds=1)
        return CompletionEnvelope(
            result=CompletionResult(
                text="generated text",
                usage=Usage(prompt_tokens=5, completion_tokens=5, total_tokens=10),
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
                    prompt_key=request.instruction_key,
                    prompt_name=metadata.name,
                    prompt_base_path=".",
                    prompt_content_hash="hash-prompt",
                    variables_hash="hash-vars",
                    user_string_hash="hash-input",
                ),
            ),
            policy_applied={"routing_reason": "test"},
            warnings=[],
        )


def test_run_missing_required_variables_returns_error(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    input_file = tmp_path / "input.txt"
    input_file.write_text("file-input", encoding="utf-8")

    metadata = PromptMetadata(
        key="daily",
        name="Daily Guidance",
        version="1.0.0",
        description="Daily guidance prompt for testing.",
        task_type="study-plan",
        required_variables=["audience"],
        optional_variables=[],
        default_variables={},
        tags=["guidance"],
    )
    stub_service = _StubService(metadata)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
        ],
    )

    assert result.exit_code == ExitCode.INPUT_ERROR
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "Missing required variables" in payload["error"]
    assert payload["trace_id"]


def test_run_invalid_input_file_returns_error(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    missing_input = tmp_path / "missing.txt"

    metadata = PromptMetadata(
        key="daily",
        name="Daily Guidance",
        version="1.0.0",
        description="Daily guidance prompt for testing.",
        task_type="study-plan",
        required_variables=["audience"],
        optional_variables=[],
        default_variables={},
        tags=["guidance"],
    )
    stub_service = _StubService(metadata)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(missing_input),
        ],
    )

    assert result.exit_code == ExitCode.INPUT_ERROR
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "Unable to read input file" in payload["error"]
    assert payload["trace_id"]


def test_run_merges_variables_and_writes_file(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    input_file = tmp_path / "input.txt"
    input_file.write_text("file-input", encoding="utf-8")

    vars_file = tmp_path / "vars.json"
    vars_file.write_text(json.dumps({"audience": "from_vars", "input_text": "vars_input"}), encoding="utf-8")

    metadata = PromptMetadata(
        key="daily",
        name="Daily Guidance",
        version="1.0.0",
        description="Daily guidance prompt for testing.",
        task_type="study-plan",
        required_variables=["audience"],
        optional_variables=["location"],
        default_variables={},
        tags=["guidance"],
    )
    stub_service = _StubService(metadata)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    output_file = tmp_path / "out.txt"
    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--vars",
            str(vars_file),
            "--var",
            "audience=from_inline",
            "--var",
            "input_text=inline_input",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "succeeded"
    assert payload["result"]["text"] == "generated text"
    assert payload["provenance"]["prompt_key"] == "daily"
    assert payload["trace_id"]

    # Inline vars override file vars, file vars override input file.
    assert stub_service.last_request.variables["audience"] == "from_inline"
    assert stub_service.last_request.variables["input_text"] == "inline_input"
    assert stub_service.last_request.user_input == "inline_input"

    written = output_file.read_text(encoding="utf-8")
    assert "TNH-Scholar Generated Content" in written
    assert "generated text" in written


def test_run_reports_invalid_vars_file(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    input_file = tmp_path / "input.txt"
    input_file.write_text("file-input", encoding="utf-8")

    broken_vars = tmp_path / "vars.json"
    broken_vars.write_text("{not-json", encoding="utf-8")

    metadata = PromptMetadata(
        key="daily",
        name="Daily Guidance",
        version="1.0.0",
        description="Daily guidance prompt for testing.",
        task_type="study-plan",
        required_variables=["audience"],
        optional_variables=[],
        default_variables={},
        tags=["guidance"],
    )
    stub_service = _StubService(metadata)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--vars",
            str(broken_vars),
        ],
    )

    assert result.exit_code == 4
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "Invalid JSON" in payload["error"]


def test_run_reports_non_object_vars_file(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    input_file = tmp_path / "input.txt"
    input_file.write_text("file-input", encoding="utf-8")

    vars_file = tmp_path / "vars.json"
    vars_file.write_text("[]", encoding="utf-8")

    metadata = PromptMetadata(
        key="daily",
        name="Daily Guidance",
        version="1.0.0",
        description="Daily guidance prompt for testing.",
        task_type="study-plan",
        required_variables=["audience"],
        optional_variables=[],
        default_variables={},
        tags=["guidance"],
    )
    stub_service = _StubService(metadata)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--vars",
            str(vars_file),
        ],
    )

    assert result.exit_code == ExitCode.INPUT_ERROR
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "--vars file must contain a JSON object" in payload["error"]


def test_cli_loads_dotenv_for_settings(tmp_path, monkeypatch):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("OPENAI_API_KEY=from_dotenv\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    env = {"OPENAI_API_KEY": None, "TNH_GEN_CONFIG_HOME": str(tmp_path / "config-home")}

    result = runner.invoke(tnh_gen.app, ["config", "get", "api_key"], env=env)

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["api_key"] == "from_dotenv"


def test_legacy_prompt_allows_auto_input_text_variable():
    metadata = PromptMetadata(
        key="legacy",
        name="Legacy Prompt",
        version="1.0.0",
        description="Legacy prompt without declared vars.",
        task_type="edit",
        required_variables=[],
        optional_variables=[],
        default_variables={},
        tags=[],
    )

    updated = run_module._ensure_input_text_variable(metadata)

    assert "input_text" in updated.optional_variables
    assert "input_text" not in metadata.optional_variables  # original untouched


def test_legacy_prompt_run_uses_fallback_metadata_and_input_text(tmp_path, monkeypatch):
    prompt_dir = _write_legacy_prompt(tmp_path)
    input_file = tmp_path / "input.txt"
    input_text = "legacy input text"
    input_file.write_text(input_text, encoding="utf-8")

    stub_service = _CatalogBackedStubService(prompt_dir)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--prompt",
            "legacy",
            "--input-file",
            str(input_file),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "succeeded"
    assert payload["prompt_warnings"]
    assert stub_service.last_request.variables["input_text"] == input_text


def test_config_set_and_get_user_scope(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.chdir(tmp_path)

    set_result = runner.invoke(tnh_gen.app, ["config", "set", "default_model", "gpt-4o"])
    assert set_result.exit_code == 0

    get_result = runner.invoke(tnh_gen.app, ["config", "get", "default_model"])
    assert get_result.exit_code == 0
    payload = json.loads(get_result.stdout)
    assert payload["default_model"] == "gpt-4o"
