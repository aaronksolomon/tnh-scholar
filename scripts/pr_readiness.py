"""Estimate PR size and run changed-file checks before opening a PR.

This script is optimized for the TNH Scholar workflow where Sourcery's
practical diff-character ceiling is the main PR-sizing constraint.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


@dataclass(frozen=True)
class DiffThresholds:
    """Diff-size thresholds for PR readiness."""

    warn_chars: int = 120_000
    limit_chars: int = 150_000


class ReadinessStatus(StrEnum):
    """PR readiness states for Sourcery review."""

    ready = "ready"
    caution = "caution"
    split_required = "split-required"


@dataclass(frozen=True)
class DiffSummary:
    """Summary of the current PR-sized diff."""

    branch: str
    compare_ref: str
    files: tuple[Path, ...]
    python_files: tuple[Path, ...]
    diff_chars: int
    status: ReadinessStatus


@dataclass(frozen=True)
class CheckCommand:
    """One suggested or executed quality-check command."""

    name: str
    argv: tuple[str, ...]


class GitDiffInspector:
    """Read changed-file and patch information from git."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    def summarize(self, *, base_ref: str, staged: bool, thresholds: DiffThresholds) -> DiffSummary:
        branch = self._run_git("branch", "--show-current").strip() or "DETACHED"
        compare_ref = "--cached" if staged else f"{base_ref}...HEAD"
        if staged:
            files = self._existing_paths(
                self._run_git("diff", "--name-only", "--diff-filter=ACMR", "--cached").splitlines()
            )
            diff_chars = len(self._run_git("diff", "--diff-filter=ACMR", "--cached"))
        else:
            compare_ref = self._working_compare_label(base_ref=base_ref)
            committed_files = self._existing_paths(
                self._run_git("diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD").splitlines()
            )
            working_files = self._existing_paths(
                self._run_git("diff", "--name-only", "--diff-filter=ACMR", "HEAD").splitlines()
            )
            untracked_files = self._existing_paths(
                self._run_git("ls-files", "--others", "--exclude-standard").splitlines()
            )
            files = self._merge_paths(committed_files, working_files, untracked_files)
            diff_chars = len(self._run_git("diff", "--diff-filter=ACMR", f"{base_ref}...HEAD"))
            diff_chars += len(self._run_git("diff", "--diff-filter=ACMR", "HEAD"))
            diff_chars += sum(self._untracked_patch_chars(path) for path in untracked_files)
        python_files = tuple(path for path in files if path.suffix == ".py")
        status = self._classify(diff_chars, thresholds)
        return DiffSummary(
            branch=branch,
            compare_ref=compare_ref,
            files=files,
            python_files=python_files,
            diff_chars=diff_chars,
            status=status,
        )

    def _run_git(self, *args: str) -> str:
        completed = subprocess.run(
            ("git", *args),
            cwd=self._repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout

    def _existing_paths(self, raw_paths: list[str]) -> tuple[Path, ...]:
        paths: list[Path] = []
        for raw_path in raw_paths:
            if not raw_path:
                continue
            path = self._repo_root / raw_path
            if path.exists():
                paths.append(Path(raw_path))
        return tuple(paths)

    def _merge_paths(self, *groups: tuple[Path, ...]) -> tuple[Path, ...]:
        ordered: dict[Path, None] = {}
        for group in groups:
            for path in group:
                ordered[path] = None
        return tuple(ordered)

    def _working_compare_label(self, *, base_ref: str) -> str:
        dirty = bool(self._run_git("status", "--short").strip())
        if dirty:
            return f"{base_ref}...HEAD (+ working tree)"
        return f"{base_ref}...HEAD"

    def _untracked_patch_chars(self, path: Path) -> int:
        completed = subprocess.run(
            ("git", "diff", "--no-index", "--", "/dev/null", str(path)),
            cwd=self._repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        return len(completed.stdout)

    def _classify(self, diff_chars: int, thresholds: DiffThresholds) -> ReadinessStatus:
        if diff_chars >= thresholds.limit_chars:
            return ReadinessStatus.split_required
        if diff_chars >= thresholds.warn_chars:
            return ReadinessStatus.caution
        return ReadinessStatus.ready


class CheckPlanner:
    """Build changed-file check commands."""

    def __init__(self, python_files: tuple[Path, ...], pytest_targets: tuple[str, ...]) -> None:
        self._python_files = python_files
        self._pytest_targets = pytest_targets

    def commands(self) -> tuple[CheckCommand, ...]:
        commands: list[CheckCommand] = []
        if self._python_files:
            python_args = tuple(str(path) for path in self._python_files)
            commands.append(
                CheckCommand(
                    name="ruff",
                    argv=("poetry", "run", "ruff", "check", *python_args),
                )
            )
            commands.append(
                CheckCommand(
                    name="mypy",
                    argv=("poetry", "run", "mypy", *python_args),
                )
            )
            commands.append(
                CheckCommand(
                    name="sourcery",
                    argv=("poetry", "run", "sourcery", "review", *python_args),
                )
            )
        if self._pytest_targets:
            commands.append(
                CheckCommand(
                    name="pytest",
                    argv=("poetry", "run", "pytest", *self._pytest_targets),
                )
            )
        return tuple(commands)


class CheckRunner:
    """Run planned quality-check commands."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    def run(self, commands: tuple[CheckCommand, ...]) -> int:
        for command in commands:
            print(f"\n[{command.name}] {' '.join(shlex.quote(part) for part in command.argv)}")
            completed = subprocess.run(command.argv, cwd=self._repo_root)
            if completed.returncode != 0:
                print(f"\n{command.name} failed with exit code {completed.returncode}.", file=sys.stderr)
                return completed.returncode
        return 0


class Reporter:
    """Render a compact readiness report."""

    def render(self, summary: DiffSummary, commands: tuple[CheckCommand, ...]) -> None:
        print("PR Readiness")
        print(f"branch: {summary.branch}")
        print(f"compare: {summary.compare_ref}")
        print(f"files: {len(summary.files)}")
        print(f"python-files: {len(summary.python_files)}")
        print(f"diff-chars: {summary.diff_chars}")
        print(f"status: {summary.status}")
        print("")
        if summary.status == ReadinessStatus.split_required:
            print("Action: split before opening a PR.")
        elif summary.status == ReadinessStatus.caution:
            print("Action: reviewable, but leave headroom for follow-up review fixes.")
        else:
            print("Action: within the preferred Sourcery diff budget.")
        print("")
        if summary.files:
            print("Changed files:")
            for path in summary.files:
                print(f"- {path}")
            print("")
        if commands:
            print("Suggested checks:")
            for command in commands:
                joined = " ".join(shlex.quote(part) for part in command.argv)
                print(f"- {joined} 2>&1" if command.name == "sourcery" else f"- {joined}")
        else:
            print("Suggested checks: none (no changed Python files or pytest targets).")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base branch or ref for diff sizing.",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Inspect staged changes instead of base...HEAD.",
    )
    parser.add_argument(
        "--run-checks",
        action="store_true",
        help="Execute the suggested changed-file checks.",
    )
    parser.add_argument(
        "--warn-chars",
        type=int,
        default=120_000,
        help="Warn when the diff reaches this many characters.",
    )
    parser.add_argument(
        "--limit-chars",
        type=int,
        default=150_000,
        help="Require a split when the diff reaches this many characters.",
    )
    parser.add_argument(
        "--pytest-target",
        action="append",
        default=[],
        help="Optional pytest target to include in the suggested or executed checks.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the readiness summary and optional checks."""
    args = parse_args()
    repo_root = Path.cwd()
    thresholds = DiffThresholds(warn_chars=args.warn_chars, limit_chars=args.limit_chars)
    inspector = GitDiffInspector(repo_root)
    summary = inspector.summarize(base_ref=args.base, staged=args.staged, thresholds=thresholds)
    planner = CheckPlanner(summary.python_files, tuple(args.pytest_target))
    commands = planner.commands()
    Reporter().render(summary, commands)
    if not args.run_checks:
        return 0
    return CheckRunner(repo_root).run(commands)


if __name__ == "__main__":
    raise SystemExit(main())
