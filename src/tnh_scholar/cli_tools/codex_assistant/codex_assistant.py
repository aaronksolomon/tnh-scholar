"""Typer entrypoint for a minimal local Codex worker wrapper.

`codex-assistant` is a thin convenience CLI for launching `codex exec`
from a predictable, sanitized user-like environment. It is intended as a
pragmatic bridge for delegated local worker invocation while the broader
orchestration surfaces are still evolving.
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
    name="codex-assistant",
    help="Minimal sanitized wrapper around `codex exec` for delegated local worker runs.",
    add_completion=False,
    no_args_is_help=True,
)


@dataclass(frozen=True)
class CodexAssistantResult:
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
class CodexAssistantPaths:
    """Resolved output paths for one invocation."""

    stdout_path: Path
    stderr_path: Path


def _validate_codex_executable(path: Path) -> Path:
    if not path.exists():
        raise typer.BadParameter(f"Codex executable does not exist: {path}")
    if not path.is_file():
        raise typer.BadParameter(f"Codex executable is not a file: {path}")
    if not os.access(path, os.X_OK):
        raise typer.BadParameter(f"Codex executable is not executable: {path}")
    return path


def _default_codex_executable() -> Path:
    env_override = os.environ.get("CODEX_EXECUTABLE") or os.environ.get(
        "CODEX_ASSISTANT_EXECUTABLE"
    )
    candidates: list[Path] = []
    if env_override:
        candidates.append(Path(env_override).expanduser())
    candidates.extend(
        [
            Path("/opt/homebrew/bin/codex"),
            Path("/usr/local/bin/codex"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return _validate_codex_executable(candidate)
    if resolved := shutil.which("codex"):
        return _validate_codex_executable(Path(resolved))
    raise typer.BadParameter(
        "Unable to locate Codex executable. Install Codex or pass --codex-executable."
    )


def _build_command(
    *,
    codex_executable: Path,
    prompt: str,
    profile: str | None,
    model: str | None,
    output_last_message_path: Path | None,
    json_output: bool,
    ephemeral: bool,
    enable_features: tuple[str, ...],
    disable_features: tuple[str, ...],
) -> tuple[str, ...]:
    command: list[str] = [str(codex_executable), "exec"]
    if json_output:
        command.append("--json")
    if ephemeral:
        command.append("--ephemeral")
    if profile:
        command.extend(["-p", profile])
    if model:
        command.extend(["-m", model])
    if output_last_message_path is not None:
        command.extend(["--output-last-message", str(output_last_message_path)])
    for feature in enable_features:
        command.extend(["--enable", feature])
    for feature in disable_features:
        command.extend(["--disable", feature])
    command.append(prompt)
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
) -> CodexAssistantPaths:
    if stdout_path is not None and stderr_path is not None:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        return CodexAssistantPaths(stdout_path=stdout_path, stderr_path=stderr_path)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    base_directory = cwd / "tmp" / "codex-assistant"
    base_directory.mkdir(parents=True, exist_ok=True)
    resolved_stdout = stdout_path or (base_directory / f"{timestamp}.stdout.jsonl")
    resolved_stderr = stderr_path or (base_directory / f"{timestamp}.stderr.log")
    resolved_stdout.parent.mkdir(parents=True, exist_ok=True)
    resolved_stderr.parent.mkdir(parents=True, exist_ok=True)
    return CodexAssistantPaths(stdout_path=resolved_stdout, stderr_path=resolved_stderr)


def _read_final_message(
    *,
    json_output: bool,
    stdout_path: Path,
    output_last_message_path: Path | None,
) -> str | None:
    if output_last_message_path is not None and output_last_message_path.exists():
        message = output_last_message_path.read_text(encoding="utf-8").strip()
        return message or None
    if not json_output or not stdout_path.exists():
        return None

    for line in _iter_lines_reverse(stdout_path):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if payload.get("type") == "item.completed":
            item = payload.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()
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


@app.command("run")
def run_command(
    prompt: str = typer.Option(..., "--prompt", help="Prompt text to pass to `codex exec`."),
    cwd: Path = typer.Option(
        Path.cwd(),
        "--cwd",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Working directory for the Codex run.",
    ),
    codex_executable: Path | None = typer.Option(
        None,
        "--codex-executable",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Optional explicit path to the Codex executable.",
    ),
    profile: str = typer.Option("collab", "--profile", help="Codex profile to use."),
    model: str | None = typer.Option(None, "--model", help="Optional model override."),
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
    output_last_message_path: Path | None = typer.Option(
        None,
        "--output-last-message-path",
        resolve_path=True,
        help="Optional path for Codex `--output-last-message` capture.",
    ),
    json_output: bool = typer.Option(
        True,
        "--json/--no-json",
        help="Request Codex JSONL stdout for machine-readable capture.",
    ),
    ephemeral: bool = typer.Option(
        True,
        "--ephemeral/--no-ephemeral",
        help="Use Codex ephemeral mode.",
    ),
    inherit_env: bool = typer.Option(
        False,
        "--inherit-env/--sanitize-env",
        help="Inherit the current environment instead of the sanitized user-like env.",
    ),
    enable_feature: list[str] = typer.Option(
        [],
        "--enable-feature",
        help="Repeatable Codex feature enable flag.",
    ),
    disable_feature: list[str] = typer.Option(
        [],
        "--disable-feature",
        help="Repeatable Codex feature disable flag.",
    ),
) -> None:
    """Run one local Codex worker invocation and emit a JSON summary."""
    resolved_cwd = cwd.resolve()
    resolved_codex = (
        _default_codex_executable()
        if codex_executable is None
        else _validate_codex_executable(codex_executable.resolve())
    )
    if not resolved_cwd.exists():
        raise typer.BadParameter(f"Working directory does not exist: {resolved_cwd}")
    paths = _resolve_capture_paths(
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        cwd=resolved_cwd,
    )
    last_message_path = output_last_message_path
    if last_message_path is not None:
        last_message_path.parent.mkdir(parents=True, exist_ok=True)
    command = _build_command(
        codex_executable=resolved_codex,
        prompt=prompt,
        profile=profile,
        model=model,
        output_last_message_path=last_message_path,
        json_output=json_output,
        ephemeral=ephemeral,
        enable_features=tuple(enable_feature),
        disable_features=tuple(disable_feature),
    )
    env = None if inherit_env else _sanitized_env(resolved_cwd)
    with paths.stdout_path.open("w", encoding="utf-8") as stdout_file:
        with paths.stderr_path.open("w", encoding="utf-8") as stderr_file:
            # `command` is an argv tuple and `shell=False`, so prompt text is
            # passed as a single argument rather than shell-interpreted.
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
    result = CodexAssistantResult(
        command=command,
        cwd=resolved_cwd,
        exit_code=completed.returncode,
        stdout_path=paths.stdout_path,
        stderr_path=paths.stderr_path,
        final_message=_read_final_message(
            json_output=json_output,
            stdout_path=paths.stdout_path,
            output_last_message_path=last_message_path,
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
