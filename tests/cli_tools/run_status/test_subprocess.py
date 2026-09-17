"""Observe flushed status while a real external-directory CLI process is live."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from tnh_scholar.cli_tools.tnh_gen.run_status.models import EventType, RunStatusEvent
from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope


def test_external_directory_live_status(tmp_path: Path, envelope: CompletionEnvelope) -> None:
    root = Path(__file__).resolve().parents[3]
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "daily.md").write_text(
        "---\nkey: daily\nname: Daily\nversion: 1.0.0\ndescription: Test\n"
        "role: test\nrequired_variables: []\n---\nRead {{ input_text }}."
    )
    (tmp_path / "input.txt").write_text("input")
    response = tmp_path / "response.json"
    response.write_text(envelope.model_dump_json())
    status, release = tmp_path / "status.jsonl", tmp_path / "release"
    environment = os.environ | {
        "PYTHONPATH": str(root / "src"),
        "TG06_PROMPTS": str(prompts),
        "TG06_RELEASE": str(release),
        "TG06_RESPONSE": str(response),
        "TNH_GEN_CONFIG_HOME": str(tmp_path / "config"),
    }
    command = [
        sys.executable,
        str(root / "tests/fixtures/tnh_gen_status_worker.py"),
        "--quiet",
        "run",
        "--api",
        "--prompt",
        "daily",
        "--prompt-dir",
        str(prompts),
        "--input-file",
        "input.txt",
        "--status-file",
        "status.jsonl",
        "--output-file",
        "result.txt",
    ]
    process = subprocess.Popen(
        command, cwd=tmp_path, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        _wait_for_heartbeat(process, status)
        assert process.poll() is None
        assert not (tmp_path / "result.txt").exists()
        release.touch()
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()
    records = [RunStatusEvent.model_validate_json(line) for line in status.read_text().splitlines()]
    assert records[-1].outcome.value == "completed"
    assert json.loads(stdout)["trace_id"] == records[-1].metadata.trace_id
    assert (tmp_path / "result.txt").is_file()
    assert [event.sequence for event in records] == list(range(1, len(records) + 1))


def _wait_for_heartbeat(process: subprocess.Popen[str], status: Path) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if status.exists():
            lines = status.read_text().splitlines(keepends=True)
            records = [RunStatusEvent.model_validate_json(line) for line in lines if line.endswith("\n")]
            if any(
                event.event_type is EventType.HEARTBEAT and event.stage.value == "generating"
                for event in records
            ):
                return
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise AssertionError(f"Worker exited early: {stdout} {stderr}")
        time.sleep(0.01)
    raise AssertionError("No live generation heartbeat before deadline")
