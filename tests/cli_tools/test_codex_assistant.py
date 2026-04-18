from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from tnh_scholar.cli_tools.codex_assistant import codex_assistant

runner = CliRunner(mix_stderr=False)


def test_codex_assistant_run_uses_sanitized_env_and_returns_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    codex_path = tmp_path / "codex"
    codex_path.write_text("", encoding="utf-8")
    codex_path.chmod(0o755)

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
        stdout.write(
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "ACK_FROM_TEST"},
                }
            )
            + "\n"
        )
        stderr.write("")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(codex_assistant.subprocess, "run", fake_run)

    result = runner.invoke(
        codex_assistant.app,
        [
            "--prompt",
            "Return ACK",
            "--cwd",
            str(cwd),
            "--codex-executable",
            str(codex_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["exit_code"] == 0
    assert payload["final_message"] == "ACK_FROM_TEST"
    assert payload["cwd"] == str(cwd.resolve())
    assert Path(payload["stdout_path"]).exists()
    assert Path(payload["stderr_path"]).exists()
    assert captured["command"] == (
        str(codex_path.resolve()),
        "exec",
        "--json",
        "--ephemeral",
        "-p",
        "collab",
        "Return ACK",
    )
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["PWD"] == str(cwd.resolve())
    assert env["TERM"] == "xterm-256color"


def test_codex_assistant_run_can_inherit_env(tmp_path: Path, monkeypatch) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    codex_path = tmp_path / "codex"
    codex_path.write_text("", encoding="utf-8")
    codex_path.chmod(0o755)

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
        del command, check, cwd, stdin, stderr, text
        nonlocal captured_env
        captured_env = env
        stdout.write("")
        return subprocess.CompletedProcess((), 0)

    monkeypatch.setattr(codex_assistant.subprocess, "run", fake_run)

    result = runner.invoke(
        codex_assistant.app,
        [
            "--prompt",
            "Return ACK",
            "--cwd",
            str(cwd),
            "--codex-executable",
            str(codex_path),
            "--inherit-env",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured_env is None


def test_codex_assistant_run_without_json_omits_final_message(tmp_path: Path, monkeypatch) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    codex_path = tmp_path / "codex"
    codex_path.write_text("", encoding="utf-8")
    codex_path.chmod(0o755)

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

    monkeypatch.setattr(codex_assistant.subprocess, "run", fake_run)

    result = runner.invoke(
        codex_assistant.app,
        [
            "--prompt",
            "Return ACK",
            "--cwd",
            str(cwd),
            "--codex-executable",
            str(codex_path),
            "--no-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["final_message"] is None
    assert "--json" not in captured["command"]
    assert Path(payload["stdout_path"]).read_text(encoding="utf-8") == "plain text output\n"


def test_codex_assistant_rejects_non_executable_path(tmp_path: Path) -> None:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    codex_path = tmp_path / "codex"
    codex_path.write_text("", encoding="utf-8")
    codex_path.chmod(0o644)

    result = runner.invoke(
        codex_assistant.app,
        [
            "--prompt",
            "Return ACK",
            "--cwd",
            str(cwd),
            "--codex-executable",
            str(codex_path),
        ],
    )

    assert result.exit_code != 0
    assert "not executable" in result.stderr
