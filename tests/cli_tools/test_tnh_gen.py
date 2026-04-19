from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent
from typing import Any

from typer.testing import CliRunner
import yaml

from tnh_scholar.cli_tools.tnh_gen import tnh_gen
from tnh_scholar.cli_tools.tnh_gen.commands import run as run_module
from tnh_scholar.cli_tools.tnh_gen.errors import ExitCode
from tnh_scholar.cli_tools.tnh_gen.config_loader import CLIConfig
from tnh_scholar.cli_tools.tnh_gen.state import ctx as cli_ctx
from tnh_scholar.gen_ai_service.models.domain import (
    AdapterDiagnostics,
    CompletionFailure,
    CompletionEnvelope,
    CompletionOutcomeStatus,
    CompletionResult,
    FailureReason,
    Fingerprint,
    Provenance,
    Usage,
)
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter
from tnh_scholar.gen_ai_service.models.errors import SafetyBlocked
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

    result = runner.invoke(tnh_gen.app, ["--api", "list"])

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


def test_list_keys_only_emits_warning_for_legacy_prompt(tmp_path, monkeypatch):
    prompt_dir = _write_legacy_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["list", "--keys-only"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "legacy"
    assert "[warn]" in result.stderr


def test_list_includes_warning_for_legacy_prompt(tmp_path, monkeypatch):
    prompt_dir = _write_legacy_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["--api", "list"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["count"] == 1
    warnings = payload["prompts"][0]["warnings"]
    assert warnings, "Expected warning for legacy prompt with missing metadata"
    assert "Expected" in warnings[0]
    assert "prompt" in warnings[0]
    assert "key" in warnings[0]
    assert "invalid-metadata" in payload["prompts"][0]["tags"]
    assert "[warn]" in result.stderr


def test_list_prompts_filters_by_tag_and_search(tmp_path, monkeypatch):
    prompt_dir = _write_prompt_catalog(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(
        tnh_gen.app,
        ["--api", "list", "--tag", "study", "--search", "Planner"],
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


def test_list_default_human_output(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["list"])

    assert result.exit_code == 0, result.output
    assert "Available Prompts" in result.stdout
    assert "Variables:" in result.stdout
    assert not result.stdout.lstrip().startswith("{")


def test_global_prompt_dir_is_applied_and_restored(tmp_path, monkeypatch):
    prompt_dir = tmp_path / "custom-prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("custom.md").write_text(
        dedent(
            """\
            ---
            key: custom
            name: Custom Prompt
            version: 1.0.0
            description: Custom prompt for testing.
            task_type: study-plan
            required_variables: []
            optional_variables: []
            default_variables: {}
            tags: []
            ---
            # Custom Prompt
            """
        ),
            encoding="utf-8",
        )
    monkeypatch.setenv("TNH_PROMPT_DIR", "sentinel")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["--prompt-dir", str(prompt_dir), "list", "--keys-only"])

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "custom"
    assert os.environ.get("TNH_PROMPT_DIR") == "sentinel"


def test_global_prompt_dir_is_restored_after_error(tmp_path, monkeypatch):
    prompt_dir = tmp_path / "custom-prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("custom.md").write_text("# Custom Prompt\n", encoding="utf-8")

    monkeypatch.setenv("TNH_PROMPT_DIR", "sentinel")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(
        tnh_gen.app,
        ["--prompt-dir", str(prompt_dir), "--api", "list", "--format", "text"],
    )

    assert result.exit_code != 0
    assert os.environ.get("TNH_PROMPT_DIR") == "sentinel"


def test_list_api_rejects_text_format(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["--api", "list", "--format", "text"])

    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "only supported without --api" in payload["error"].lower()
    assert "trace_id=" in result.stderr


def test_list_api_rejects_table_format(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))

    result = runner.invoke(tnh_gen.app, ["--api", "list", "--format", "table"])

    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "only supported without --api" in payload["error"].lower()
    assert "trace_id=" in result.stderr


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
        return CompletionEnvelope(
            outcome=CompletionOutcomeStatus.SUCCEEDED,
            result=CompletionResult(
                text="generated text",
                usage=Usage(
                    prompt_tokens=10, completion_tokens=20, total_tokens=30
                ),
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


class _IncompleteStubService:
    def __init__(self, metadata: PromptMetadata):
        self.last_request: Any = None
        self.catalog = _StubCatalog(metadata)
        self._metadata = metadata

    def generate(self, request):
        self.last_request = request
        started = datetime.now()
        finished = started + timedelta(seconds=1)
        return CompletionEnvelope(
            outcome=CompletionOutcomeStatus.INCOMPLETE,
            result=CompletionResult(
                text="partial text",
                usage=Usage(
                    prompt_tokens=8,
                    completion_tokens=12,
                    total_tokens=20,
                ),
                model="gpt-4o",
                provider="openai",
                finish_reason="length",
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
            warnings=["provider-status:incomplete"],
        )


class _FailedStubService:
    def __init__(self, metadata: PromptMetadata):
        self.last_request: Any = None
        self.catalog = _StubCatalog(metadata)
        self._metadata = metadata

    def generate(self, request):
        self.last_request = request
        started = datetime.now()
        finished = started + timedelta(seconds=1)
        return CompletionEnvelope(
            outcome=CompletionOutcomeStatus.FAILED,
            failure=CompletionFailure(
                reason=FailureReason.CONTENT_EXTRACTION_ERROR,
                message="backend failure",
                retryable=False,
                adapter_diagnostics=AdapterDiagnostics(
                    content_source="choices[0].message.content",
                    content_part_count=None,
                    raw_finish_reason="stop",
                    extraction_notes="adapter could not parse content",
                ),
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
            warnings=["provider-status:failed"],
        )


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
            outcome=CompletionOutcomeStatus.SUCCEEDED,
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


class _BudgetBlockedService:
    def __init__(self, metadata: PromptMetadata):
        self.last_request: Any = None
        self.catalog = _StubCatalog(metadata)

    def generate(self, request):
        self.last_request = request
        raise SafetyBlocked(
            "Estimated cost 0.0420 exceeds budget 0.0200",
            blocked_reason="budget",
            estimated_cost=0.042,
            max_dollars=0.02,
        )


class _RecordingFactory:
    def __init__(self, service: Any):
        self.service = service
        self.last_config: CLIConfig | None = None
        self.last_overrides: Any = None

    def create_genai_service(self, cli_config: CLIConfig, overrides: Any):
        self.last_config = cli_config
        self.last_overrides = overrides
        return self.service


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
            "--api",
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
    assert "trace_id=" in result.stderr


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
            "--api",
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
    assert "trace_id=" in result.stderr


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
            "--api",
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
    assert result.stderr == ""
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
    assert "tnh_scholar_generated: true" in written
    assert "prompt_key: daily" in written
    assert "generated text" in written


def test_run_strips_input_frontmatter_and_merges_output_metadata(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    input_file = tmp_path / "input.md"
    input_file.write_text(
        (
            "---\n"
            "source: draft\n"
            "prompt_key: user-value\n"
            "---\n"
            "file-input\n"
        ),
        encoding="utf-8",
    )

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

    output_file = tmp_path / "out.txt"
    result = runner.invoke(
        tnh_gen.app,
        [
            "--api",
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--var",
            "audience=students",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    assert stub_service.last_request.user_input.strip() == "file-input"
    assert stub_service.last_request.variables["input_text"].strip() == "file-input"

    written = output_file.read_text(encoding="utf-8")
    header, body = written.split("---\n", 2)[1:]
    payload = yaml.safe_load(header)

    assert payload["source"] == "draft"
    assert payload["prompt_key"] == "daily"
    assert payload["tnh_scholar_generated"] is True
    assert body.lstrip("\n") == "generated text"


def test_run_preserves_yaml_date_frontmatter(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    input_file = tmp_path / "input.md"
    input_file.write_text(
        (
            "---\n"
            "date: 2026-04-17\n"
            "source: draft\n"
            "---\n"
            "file-input\n"
        ),
        encoding="utf-8",
    )

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

    output_file = tmp_path / "out.txt"
    result = runner.invoke(
        tnh_gen.app,
        [
            "--api",
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--var",
            "audience=students",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    written = output_file.read_text(encoding="utf-8")
    header = written.split("---\n", 2)[1]
    payload = yaml.safe_load(header)
    assert payload["date"] == "2026-04-17"


def test_run_accepts_forwarded_config_api_and_prompt_dir(tmp_path, monkeypatch):
    prompt_dir = _write_prompt(tmp_path)
    input_file = tmp_path / "input.txt"
    input_file.write_text("file-input", encoding="utf-8")

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "default_model": "from-config",
                "prompt_catalog_dir": str(tmp_path / "wrong-prompts"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

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
    factory = _RecordingFactory(_StubService(metadata))

    monkeypatch.delenv("TNH_PROMPT_DIR", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(cli_ctx, "service_factory", factory)

    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--config",
            str(config_path),
            "--api",
            "--prompt-dir",
            str(prompt_dir),
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--var",
            "audience=students",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "succeeded"
    assert factory.last_config is not None
    assert factory.last_config.default_model == "from-config"
    assert factory.last_config.prompt_catalog_dir == Path(prompt_dir)


def test_run_api_incomplete_returns_payload_and_writes_file(tmp_path, monkeypatch):
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
    stub_service = _IncompleteStubService(metadata)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    output_file = tmp_path / "incomplete.txt"
    result = runner.invoke(
        tnh_gen.app,
        [
            "--api",
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--var",
            "audience=students",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "incomplete"
    assert payload["result"]["text"] == "partial text"
    assert payload["result"]["finish_reason"] == "length"
    assert payload["provenance"]["prompt_key"] == "daily"
    assert output_file.exists()
    assert "partial text" in output_file.read_text(encoding="utf-8")


def test_run_api_failed_completion_returns_failure_payload_without_file(tmp_path, monkeypatch):
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
    stub_service = _FailedStubService(metadata)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    output_file = tmp_path / "failed.txt"
    result = runner.invoke(
        tnh_gen.app,
        [
            "--api",
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--var",
            "audience=students",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == ExitCode.PROVIDER_ERROR
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert payload["failure"]["reason"] == FailureReason.CONTENT_EXTRACTION_ERROR.value
    assert payload["failure"]["message"] == "backend failure"
    assert payload["failure"]["adapter_diagnostics"]["content_source"] == "choices[0].message.content"
    assert not output_file.exists()


def test_run_api_budget_block_returns_structured_payload(tmp_path, monkeypatch):
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
    factory = _RecordingFactory(_BudgetBlockedService(metadata))

    monkeypatch.delenv("TNH_PROMPT_DIR", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(cli_ctx, "service_factory", factory)

    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--api",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--var",
            "audience=students",
        ],
    )

    assert result.exit_code == ExitCode.POLICY_ERROR
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["blocked_reason"] == "budget"
    assert payload["estimated_cost"] == 0.042
    assert payload["max_dollars"] == 0.02
    assert payload["trace_id"]


def test_run_human_budget_block_reports_actionable_text(tmp_path, monkeypatch):
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
    factory = _RecordingFactory(_BudgetBlockedService(metadata))

    monkeypatch.delenv("TNH_PROMPT_DIR", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(cli_ctx, "service_factory", factory)

    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--var",
            "audience=students",
        ],
    )

    assert result.exit_code == ExitCode.POLICY_ERROR
    assert "Budget blocked" in result.stdout
    assert "Raise max_dollars in config" in result.stdout
    assert "tnh-gen config set --workspace max_dollars 0.10" in result.stdout
    assert "trace_id=" in result.stderr


def test_run_human_mode_failed_completion_reports_error_and_skips_output_file(tmp_path, monkeypatch):
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
    stub_service = _FailedStubService(metadata)

    monkeypatch.setenv("TNH_PROMPT_DIR", prompt_dir)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config-home"))
    monkeypatch.setattr(run_module, "_initialize_service", lambda *_, **__: stub_service)

    output_file = tmp_path / "failed.txt"
    result = runner.invoke(
        tnh_gen.app,
        [
            "run",
            "--prompt",
            "daily",
            "--input-file",
            str(input_file),
            "--var",
            "audience=students",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == ExitCode.PROVIDER_ERROR
    assert "Error:" in result.stdout
    assert "backend failure" in result.stdout
    assert "[warn]" in result.stderr
    assert "trace_id=" in result.stderr
    assert not output_file.exists()


def test_run_human_mode_outputs_text_only(tmp_path, monkeypatch):
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
            "--var",
            "audience=students",
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "generated text"
    assert not result.stdout.lstrip().startswith("{")


def test_run_human_mode_rejects_json_format(tmp_path, monkeypatch):
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
            "--var",
            "audience=students",
            "--format",
            "json",
        ],
    )

    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "requires --api" in result.stdout
    assert "trace_id=" in result.stderr


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
            "--api",
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
            "--api",
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

    result = runner.invoke(tnh_gen.app, ["--api", "config", "get", "api_key"], env=env)

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["api_key"] == "from_dotenv"


def test_config_show_human_outputs_yaml(tmp_path, monkeypatch):
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    config_home.joinpath("tnh-gen.json").write_text(
        json.dumps({"default_model": "gpt-4o-mini"}, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(config_home))

    result = runner.invoke(tnh_gen.app, ["config", "show"])

    assert result.exit_code == 0, result.output
    assert "default_model: gpt-4o-mini" in result.stdout
    assert not result.stdout.lstrip().startswith("{")


def test_config_show_human_outputs_text(tmp_path, monkeypatch):
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    config_home.joinpath("tnh-gen.json").write_text(
        json.dumps({"default_model": "gpt-4o-mini"}, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(config_home))

    result = runner.invoke(tnh_gen.app, ["config", "show", "--format", "text"])

    assert result.exit_code == 0, result.output
    assert "default_model: gpt-4o-mini" in result.stdout


def test_config_get_human_outputs_yaml(tmp_path, monkeypatch):
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    config_home.joinpath("tnh-gen.json").write_text(
        json.dumps({"default_model": "gpt-4o-mini"}, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(config_home))

    result = runner.invoke(tnh_gen.app, ["config", "get", "default_model"])

    assert result.exit_code == 0, result.output
    assert "default_model: gpt-4o-mini" in result.stdout
    assert not result.stdout.lstrip().startswith("{")


def test_config_show_format_json_without_api_is_rejected(tmp_path, monkeypatch):
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    config_home.joinpath("tnh-gen.json").write_text(
        json.dumps({"default_model": "gpt-4o-mini"}, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(config_home))

    result = runner.invoke(tnh_gen.app, ["config", "show", "--format", "json"])

    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "requires --api" in result.stdout
    assert "trace_id=" in result.stderr


def test_version_human_outputs_multiline_text():
    result = runner.invoke(tnh_gen.app, ["version"])

    assert result.exit_code == 0, result.output
    stdout = result.stdout
    assert stdout.strip()
    assert stdout.lstrip().startswith("tnh-gen ")
    assert "python" in stdout.lower()
    assert "platform" in stdout.lower()
    assert not stdout.lstrip().startswith("{")


def test_version_api_outputs_json():
    result = runner.invoke(tnh_gen.app, ["--api", "version"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)
    assert "tnh_gen" in payload
    assert "python" in payload
    assert "platform" in payload
    assert "trace_id" in payload
    assert payload["trace_id"]


def test_version_format_json_without_api_is_rejected():
    result = runner.invoke(tnh_gen.app, ["version", "--format", "json"])

    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "requires --api" in result.stdout
    assert "trace_id=" in result.stderr


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
            "--api",
            "run",
            "--prompt",
            "legacy",
            "--input-file",
            str(input_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.stderr == ""
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

    set_result = runner.invoke(
        tnh_gen.app, ["--api", "config", "set", "default_model", "gpt-4o"]
    )
    assert set_result.exit_code == 0

    get_result = runner.invoke(tnh_gen.app, ["--api", "config", "get", "default_model"])
    assert get_result.exit_code == 0
    payload = json.loads(get_result.stdout)
    assert payload["default_model"] == "gpt-4o"
