"""CLI integration through the real preparation/output paths."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from tnh_scholar.cli_tools.tnh_gen import tnh_gen
from tnh_scholar.cli_tools.tnh_gen.commands import run as run_module
from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunStatusEvent
from tnh_scholar.cli_tools.tnh_gen.state import ctx
from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope
from tnh_scholar.prompt_system.domain.models import PromptMetadata


@pytest.fixture
def invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, envelope: CompletionEnvelope):
    service = Mock()
    service.generate.return_value = envelope
    service.catalog.introspect.return_value = PromptMetadata(
        key="daily", name="Daily", version="1.0.0", description="Test", role="test", required_variables=[]
    )
    service.catalog.catalog_health.return_value.error_count = 0
    factory = Mock()
    factory.create_genai_service.return_value = service
    monkeypatch.setattr(ctx, "service_factory", factory)
    monkeypatch.setenv("TNH_GEN_CONFIG_HOME", str(tmp_path / "config"))
    source = tmp_path / "input.txt"
    source.write_text("private input")
    return ["run", "--prompt", "daily", "--input-file", str(source)], service


@pytest.mark.parametrize("flags", [["--api"], ["--api", "--quiet"], []])
def test_status_with_output_and_trace(tmp_path: Path, invocation, flags: list[str]) -> None:
    args, service = invocation
    status, output = tmp_path / "status.jsonl", tmp_path / "result.txt"
    result = CliRunner(mix_stderr=False).invoke(
        tnh_gen.app, flags + args + ["--status-file", str(status), "--output-file", str(output)]
    )
    assert result.exit_code == 0, result.output
    events = [RunStatusEvent.model_validate_json(line) for line in status.read_text().splitlines()]
    assert [e.stage.value for e in events] == [
        "starting",
        "preparing_run",
        "generating",
        "emitting_output",
        "emitting_output",
    ]
    assert events[-1].outcome.value == "completed"
    assert events[-1].model == "resolved-model"
    assert events[0].model is None
    assert output.is_file()
    assert "private input" not in status.read_text()
    if "--api" in flags:
        import json

        assert json.loads(result.stdout)["trace_id"] == events[-1].metadata.trace_id
    service.generate.assert_called_once()


@pytest.mark.parametrize(
    "destination",
    ["input.txt", "result.txt", "result.txt.provenance.yaml", "missing/status", "existing", "symlink"],
)
def test_invalid_status_path_prevents_service(tmp_path: Path, invocation, destination: str) -> None:
    args, service = invocation
    (tmp_path / "existing").write_text("preserve")
    (tmp_path / "symlink").symlink_to(tmp_path / "absent")
    result = CliRunner(mix_stderr=False).invoke(
        tnh_gen.app,
        ["--api"]
        + args
        + ["--status-file", str(tmp_path / destination), "--output-file", str(tmp_path / "result.txt")],
    )
    assert result.exit_code == 5
    service.generate.assert_not_called()
    assert (tmp_path / "existing").read_text() == "preserve"
    assert not (tmp_path / "absent").exists()


def test_output_failure_preserves_generated_call(
    tmp_path: Path, invocation, monkeypatch: pytest.MonkeyPatch
) -> None:
    args, service = invocation
    writer = Mock(side_effect=OSError("disk full"))
    monkeypatch.setattr(run_module, "write_output_file", writer)
    status = tmp_path / "status"
    result = CliRunner(mix_stderr=False).invoke(
        tnh_gen.app,
        ["--api"] + args + ["--status-file", str(status), "--output-file", str(tmp_path / "output")],
    )
    terminal = RunStatusEvent.model_validate_json(status.read_text().splitlines()[-1])
    assert terminal.failure.origin_stage.value == "emitting_output"
    assert result.exit_code == terminal.exit_code == 3
    service.generate.assert_called_once()


def test_failed_envelope_is_reported_at_generation(
    tmp_path: Path, invocation, envelope: CompletionEnvelope
) -> None:
    from tnh_scholar.gen_ai_service.models.domain import (
        CompletionFailure,
        CompletionOutcomeStatus,
        FailureReason,
    )

    args, service = invocation
    service.generate.return_value = envelope.model_copy(
        update={
            "outcome": CompletionOutcomeStatus.FAILED,
            "result": None,
            "failure": CompletionFailure(
                reason=FailureReason.CONTRACT_VALIDATION_FAILED, message="invalid", retryable=False
            ),
        }
    )
    status = tmp_path / "events"
    result = CliRunner(mix_stderr=False).invoke(
        tnh_gen.app, ["--api"] + args + ["--status-file", str(status)]
    )
    event = RunStatusEvent.model_validate_json(status.read_text().splitlines()[-1])
    assert result.exit_code == event.exit_code == 4
    assert event.stage.value == "emitting_output"
    assert event.failure.origin_stage.value == "generating"
    assert event.reporting_failure is None
    service.generate.assert_called_once()


def test_status_initialization_io_error_skips_preparation(
    tmp_path: Path, invocation, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tnh_scholar.cli_tools.tnh_gen.run_status.sinks.jsonl import JsonlRunStatusSink

    args, service = invocation
    monkeypatch.setattr(JsonlRunStatusSink, "open", Mock(side_effect=PermissionError()))
    result = CliRunner(mix_stderr=False).invoke(
        tnh_gen.app, ["--api"] + args + ["--status-file", str(tmp_path / "events")]
    )
    assert result.exit_code == 5
    service.generate.assert_not_called()
    service.catalog.introspect.assert_not_called()


def test_non_tty_default_keeps_stdout_plain(invocation) -> None:
    args, service = invocation
    result = CliRunner(mix_stderr=False).invoke(tnh_gen.app, args)
    assert result.exit_code == 0
    assert result.stdout == "generated text\n"
    assert "starting" not in result.stderr
    service.generate.assert_called_once()


@pytest.mark.parametrize("destination", [".tnh-gen.json", ".vscode/tnh-scholar.json", "config/tnh-gen.json"])
def test_implicit_config_paths_remain_absent(
    tmp_path: Path, invocation, monkeypatch: pytest.MonkeyPatch, destination: str
) -> None:
    args, service = invocation
    monkeypatch.chdir(tmp_path)
    path = tmp_path / destination
    path.parent.mkdir(parents=True, exist_ok=True)
    result = CliRunner(mix_stderr=False).invoke(tnh_gen.app, ["--api"] + args + ["--status-file", str(path)])
    assert result.exit_code == 5
    assert not path.exists()
    service.generate.assert_not_called()


def test_payload_failure_is_output_failure(
    tmp_path: Path, invocation, monkeypatch: pytest.MonkeyPatch
) -> None:
    args, service = invocation
    monkeypatch.setattr(run_module, "_build_success_payload", Mock(side_effect=ValueError("invalid payload")))
    status = tmp_path / "events"
    result = CliRunner(mix_stderr=False).invoke(
        tnh_gen.app, ["--api"] + args + ["--status-file", str(status)]
    )
    events = [RunStatusEvent.model_validate_json(line) for line in status.read_text().splitlines()]
    assert result.exit_code != 0
    assert events[-1].failure.origin_stage.value == "emitting_output"
    assert (
        sum(e.event_type.value == "stage_started" and e.stage.value == "emitting_output" for e in events) == 1
    )
    service.generate.assert_called_once()
