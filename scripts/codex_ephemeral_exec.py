#!/usr/bin/env python3
"""Run Codex headlessly with stdout/stderr capture.

This is an experiment helper for OA01.4 communication work. It intentionally
stays small and relies on the caller's existing shell environment, auth, and
home-state rather than trying to virtualize Codex execution.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--stdout-path", required=True)
    parser.add_argument("--stderr-path", required=True)
    parser.add_argument(
        "--codex-path",
        default=(
            "/Users/phapman/.vscode/extensions/openai.chatgpt-26.406.31014-darwin-arm64/"
            "bin/macos-aarch64/codex"
        ),
    )
    parser.add_argument("--cwd")
    parser.add_argument("--model", default="gpt-5.2-codex")
    return parser.parse_args()


def run_codex(args: argparse.Namespace) -> int:
    """Run Codex once and capture stdout/stderr."""
    stdout_path = Path(args.stdout_path)
    stderr_path = Path(args.stderr_path)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        args.codex_path,
        "exec",
        "--json",
        "--ephemeral",
        "-m",
        args.model,
        args.prompt,
    ]
    with stdout_path.open("w", encoding="utf-8") as stdout_file:
        with stderr_path.open("w", encoding="utf-8") as stderr_file:
            completed = subprocess.run(
                command,
                check=False,
                cwd=args.cwd,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
            )
    return completed.returncode


def read_final_message(stdout_path: Path) -> str | None:
    """Extract the last agent message from Codex JSONL output."""
    if not stdout_path.exists():
        return None
    for line in reversed(stdout_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("type") != "item.completed":
            continue
        item = payload.get("item")
        if not isinstance(item, dict) or item.get("type") != "agent_message":
            continue
        message = item.get("text")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return None


def main() -> int:
    """Run the helper and print a tiny summary."""
    args = parse_args()
    exit_code = run_codex(args)
    final_message = read_final_message(Path(args.stdout_path))
    print(
        json.dumps(
            {
                "exit_code": exit_code,
                "stdout_path": args.stdout_path,
                "stderr_path": args.stderr_path,
                "cwd": args.cwd,
                "final_message": final_message,
            }
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
