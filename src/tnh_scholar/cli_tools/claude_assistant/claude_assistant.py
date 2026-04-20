"""Typer entrypoint for a minimal local Claude worker wrapper.

`claude-assistant` is a thin convenience CLI for launching `claude --print`
from a predictable environment. It is intended as a pragmatic bridge for
delegated local worker invocation while the broader orchestration surfaces are
still evolving.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import typer

app = typer.Typer(
    name="claude-assistant",
    help="Minimal wrapper around `claude --print` for delegated local worker runs.",
    add_completion=False,
    no_args_is_help=True,
)


@dataclass(frozen=True)
class ClaudeAssistantResult:
    """Serializable summary of one wrapper invocation."""

    command: tuple[str, ...]
    cwd: Path
    exit_code: int
    stdout_path: Path
    stderr_path: Path
    final_message: str | None

    def to_json(self) -> str:
        """Render one JSON summary suitable for scripted callers."""
        return json.dumps(
            {
                "command": list(self.command),
                "cwd": str(self.cwd),
                "exit_code": self.exit_code,
                "stdout_path": str(self.stdout_path),
                "stderr_path": str(self.stderr_path),
                "final_message": self.final_message,
            }
        )


@dataclass(frozen=True)
class ClaudeAssistantPaths:
    """Resolved output paths for one invocation."""

    stdout_path: Path
    stderr_path: Path


def _validate_claude_executable(path: Path) -> Path:
    if not path.exists():
        raise typer.BadParameter(f"Claude executable does not exist: {path}")
    if not path.is_file():
        raise typer.BadParameter(f"Claude executable is not a file: {path}")
    if not os.access(path, os.X_OK):
        raise typer.BadParameter(f"Claude executable is not executable: {path}")
    return path


def _default_claude_executable() -> Path:
    env_override = os.environ.get("CLAUDE_EXECUTABLE") or os.environ.get(
        "CLAUDE_ASSISTANT_EXECUTABLE"
    )
    candidates: list[Path] = []
    if env_override:
        candidates.append(Path(env_override).expanduser())
    candidates.extend(
        [
            Path("/opt/homebrew/bin/claude"),
            Path("/usr/local/bin/claude"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return _validate_claude_executable(candidate)
    if resolved := shutil.which("claude"):
        return _validate_claude_executable(Path(resolved))
    raise typer.BadParameter(
        "Unable to locate Claude executable. Install Claude or pass --claude-executable."
    )


def _build_command(
    *,
    claude_executable: Path,
    prompt: str,
    permission_mode: str,
    json_output: bool,
    verbose: bool,
) -> tuple[str, ...]:
    command: list[str] = [str(claude_executable), "--print"]
    if verbose:
        command.append("--verbose")
    if json_output:
        command.extend(["--output-format", "stream-json"])
    command.extend(["--permission-mode", permission_mode, prompt])
    return tuple(command)


def _sanitized_env(cwd: Path) -> dict[str, str]:
    source = os.environ
    path_value = source.get("PATH", "")
    sanitized_path = path_value or "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    env: dict[str, str] = {
        "HOME": source.get("HOME", str(Path.home())),
        "PATH": sanitized_path,
        "SHELL": source.get("SHELL", "/bin/zsh"),
        "TERM": source.get("TERM", "xterm-256color")
        if source.get("TERM", "xterm-256color") != "dumb"
        else "xterm-256color",
        "TMPDIR": source.get("TMPDIR", "/tmp"),
        "PWD": str(cwd),
    }
    for key in ("LANG", "LC_ALL", "LC_CTYPE", "USER", "LOGNAME", "SSH_AUTH_SOCK"):
        if value := source.get(key):
            env[key] = value
    return env


def _resolve_capture_paths(
    *,
    stdout_path: Path | None,
    stderr_path: Path | None,
    cwd: Path,
) -> ClaudeAssistantPaths:
    if stdout_path is not None and stderr_path is not None:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        return ClaudeAssistantPaths(stdout_path=stdout_path, stderr_path=stderr_path)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    base_directory = cwd / "tmp" / "claude-assistant"
    base_directory.mkdir(parents=True, exist_ok=True)
    resolved_stdout = stdout_path or (base_directory / f"{timestamp}.stdout.jsonl")
    resolved_stderr = stderr_path or (base_directory / f"{timestamp}.stderr.log")
    resolved_stdout.parent.mkdir(parents=True, exist_ok=True)
    resolved_stderr.parent.mkdir(parents=True, exist_ok=True)
    return ClaudeAssistantPaths(stdout_path=resolved_stdout, stderr_path=resolved_stderr)


def _read_final_message(*, json_output: bool, stdout_path: Path) -> str | None:
    if not json_output or not stdout_path.exists():
        return None
    for line in _iter_lines_reverse(stdout_path):
        candidate = _extract_text_candidate(line)
        if candidate:
            return candidate
    return None


def _iter_lines_reverse(path: Path, chunk_size: int = 8192) -> list[str]:
    lines: list[str] = []
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        position = handle.tell()
        remainder = b""
        while position > 0:
            read_size = min(chunk_size, position)
            position -= read_size
            handle.seek(position)
            chunk = handle.read(read_size)
            parts = (chunk + remainder).splitlines()
            if position > 0:
                remainder = parts[0]
                parts = parts[1:]
            else:
                remainder = b""
            lines.extend(part.decode("utf-8", errors="replace") for part in reversed(parts))
        if remainder:
            lines.append(remainder.decode("utf-8", errors="replace"))
    return lines


def _extract_text_candidate(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if not _is_final_response_payload(payload):
        return None
    for key in ("text", "result", "content"):
        rendered = _render_candidate(payload.get(key))
        if rendered:
            return rendered
    return None


def _is_final_response_payload(payload: dict[str, object]) -> bool:
    payload_type = payload.get("type")
    if payload_type in {"assistant", "assistant_message", "message", "result", "complete"}:
        return True
    message = payload.get("message")
    if isinstance(message, dict) and message.get("role") == "assistant":
        return True
    return False


def _render_candidate(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        for key in ("text", "output", "summary"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return None


@app.command("run")
def run_command(
    prompt: str = typer.Option(..., "--prompt", help="Prompt text to pass to `claude --print`."),
    cwd: Path = typer.Option(
        Path.cwd(),
        "--cwd",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Working directory for the Claude run.",
    ),
    claude_executable: Path | None = typer.Option(
        None,
        "--claude-executable",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Optional explicit path to the Claude executable.",
    ),
    stdout_path: Path | None = typer.Option(
        None,
        "--stdout-path",
        resolve_path=True,
        help="Optional path for captured stdout.",
    ),
    stderr_path: Path | None = typer.Option(
        None,
        "--stderr-path",
        resolve_path=True,
        help="Optional path for captured stderr.",
    ),
    permission_mode: str = typer.Option(
        "dontAsk",
        "--permission-mode",
        help="Claude permission mode, for example `dontAsk` or `acceptEdits`.",
    ),
    json_output: bool = typer.Option(
        True,
        "--json/--no-json",
        help="Request Claude stream-json stdout for machine-readable capture.",
    ),
    verbose: bool = typer.Option(
        True,
        "--verbose/--no-verbose",
        help="Include Claude verbose event output.",
    ),
    inherit_env: bool = typer.Option(
        False,
        "--inherit-env/--sanitize-env",
        help="Inherit the current environment instead of the sanitized env.",
    ),
) -> None:
    """Run one local Claude worker invocation and emit a JSON summary."""
    resolved_cwd = cwd.resolve()
    resolved_claude = (
        _default_claude_executable()
        if claude_executable is None
        else _validate_claude_executable(claude_executable.resolve())
    )
    if not resolved_cwd.exists():
        raise typer.BadParameter(f"Working directory does not exist: {resolved_cwd}")
    paths = _resolve_capture_paths(
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        cwd=resolved_cwd,
    )
    command = _build_command(
        claude_executable=resolved_claude,
        prompt=prompt,
        permission_mode=permission_mode,
        json_output=json_output,
        verbose=verbose,
    )
    env = None if inherit_env else _sanitized_env(resolved_cwd)
    with paths.stdout_path.open("w", encoding="utf-8") as stdout_file:
        with paths.stderr_path.open("w", encoding="utf-8") as stderr_file:
            completed = subprocess.run(
                command,
                check=False,
                cwd=resolved_cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
            )
    result = ClaudeAssistantResult(
        command=command,
        cwd=resolved_cwd,
        exit_code=completed.returncode,
        stdout_path=paths.stdout_path,
        stderr_path=paths.stderr_path,
        final_message=_read_final_message(
            json_output=json_output,
            stdout_path=paths.stdout_path,
        ),
    )
    typer.echo(result.to_json())
    if completed.returncode != 0:
        raise typer.Exit(code=completed.returncode)


def main() -> None:
    """Dispatch to the Typer app."""
    app()


if __name__ == "__main__":
    main()
