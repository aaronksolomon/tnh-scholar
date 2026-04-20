from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from tnh_scholar.cli_tools.claude_assistant import claude_assistant

runner = CliRunner(mix_stderr=False)


def test_claude_assistant_run_uses_sanitized_env_and_returns_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    claude_path = tmp_path / "claude"
    claude_path.write_text("", encoding="utf-8")
    claude_path.chmod(0o755)

    captured: dict[str, object] = {}

    def fake_run(
        command: tuple[str, ...],
        *,
        check: bool,
        cwd: Path,
        env: dict[str, str] | None,
        stdin,
        stdout,
        stderr,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, stdin, text
        captured["command"] = command
        captured["cwd"] = cwd
        captured["env"] = env
        stdout.write(json.dumps({"type": "assistant", "text": "ACK_FROM_CLAUDE_TEST"}) + "\n")
        stderr.write("")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(claude_assistant.subprocess, "run", fake_run)

    result = runner.invoke(
        claude_assistant.app,
        [
            "--prompt",
            "Return ACK",
            "--cwd",
            str(cwd),
            "--claude-executable",
            str(claude_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["exit_code"] == 0
    assert payload["final_message"] == "ACK_FROM_CLAUDE_TEST"
    assert payload["cwd"] == str(cwd.resolve())
    assert Path(payload["stdout_path"]).exists()
    assert Path(payload["stderr_path"]).exists()
    assert captured["command"] == (
        str(claude_path.resolve()),
        "--print",
        "--verbose",
        "--output-format",
        "stream-json",
        "--permission-mode",
        "dontAsk",
        "Return ACK",
    )
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["PWD"] == str(cwd.resolve())
    assert env["TERM"] == "xterm-256color"


def test_claude_assistant_run_can_inherit_env(tmp_path: Path, monkeypatch) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    claude_path = tmp_path / "claude"
    claude_path.write_text("", encoding="utf-8")
    claude_path.chmod(0o755)

    captured_env: dict[str, str] | None = None

    def fake_run(
        command: tuple[str, ...],
        *,
        check: bool,
        cwd: Path,
        env: dict[str, str] | None,
        stdin,
        stdout,
        stderr,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del command, check, cwd, stdin, stdout, stderr, text
        nonlocal captured_env
        captured_env = env
        return subprocess.CompletedProcess((), 0)

    monkeypatch.setattr(claude_assistant.subprocess, "run", fake_run)

    result = runner.invoke(
        claude_assistant.app,
        [
            "--prompt",
            "Return ACK",
            "--cwd",
            str(cwd),
            "--claude-executable",
            str(claude_path),
            "--inherit-env",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured_env is None


def test_claude_assistant_run_without_json_omits_final_message(tmp_path: Path, monkeypatch) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    claude_path = tmp_path / "claude"
    claude_path.write_text("", encoding="utf-8")
    claude_path.chmod(0o755)

    captured: dict[str, object] = {}

    def fake_run(
        command: tuple[str, ...],
        *,
        check: bool,
        cwd: Path,
        env: dict[str, str] | None,
        stdin,
        stdout,
        stderr,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, cwd, env, stdin, stderr, text
        captured["command"] = command
        stdout.write("plain text output\n")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(claude_assistant.subprocess, "run", fake_run)

    result = runner.invoke(
        claude_assistant.app,
        [
            "--prompt",
            "Return ACK",
            "--cwd",
            str(cwd),
            "--claude-executable",
            str(claude_path),
            "--no-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["final_message"] is None
    assert "--output-format" not in captured["command"]
    assert Path(payload["stdout_path"]).read_text(encoding="utf-8") == "plain text output\n"


def test_claude_assistant_rejects_non_executable_path(tmp_path: Path) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    claude_path = tmp_path / "claude"
    claude_path.write_text("", encoding="utf-8")
    claude_path.chmod(0o644)

    result = runner.invoke(
        claude_assistant.app,
        [
            "--prompt",
            "Return ACK",
            "--cwd",
            str(cwd),
            "--claude-executable",
            str(claude_path),
        ],
    )

    assert result.exit_code != 0
    assert "not executable" in result.stderr
