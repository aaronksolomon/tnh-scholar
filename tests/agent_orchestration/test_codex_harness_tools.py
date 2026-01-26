"""Tests for Codex harness tools."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.codex_harness.models import PatchApplyResult, TestRunResult
from tnh_scholar.agent_orchestration.codex_harness.providers.patch_applier import GitPatchApplier
from tnh_scholar.agent_orchestration.codex_harness.providers.tool_executor import CodexToolExecutor
from tnh_scholar.agent_orchestration.codex_harness.tools import (
    ApplyPatchArgs,
    ListFilesArgs,
    ReadFileArgs,
    RunTestsArgs,
    SearchRepoArgs,
    ToolCall,
    ToolName,
)


@dataclass(frozen=True)
class FixedWorkspace:
    root: Path

    def repo_root(self) -> Path:
        return self.root


@dataclass(frozen=True)
class FakeSearcher:
    matches: list[str]

    def search(self, query: str, root: Path) -> list[str]:
        _ = (query, root)
        return list(self.matches)


@dataclass(frozen=True)
class FakeTestRunner:
    result: TestRunResult

    def run(self, command: str, timeout_seconds: int) -> TestRunResult:
        _ = (command, timeout_seconds)
        return self.result


def test_read_file_tool(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("hello", encoding="utf-8")
    executor = CodexToolExecutor(
        workspace=FixedWorkspace(tmp_path),
        patch_applier=GitPatchApplier(),
        test_runner=FakeTestRunner(TestRunResult(exit_code=0, stdout="", stderr="")),
        searcher=FakeSearcher(matches=[]),
        test_timeout_seconds=1,
    )
    args = ReadFileArgs(path="sample.txt").model_dump_json()
    result = executor.execute(ToolCall(name=ToolName.read_file, call_id="c1", arguments_json=args))
    assert "hello" in result.output_json


def test_list_files_tool(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    executor = CodexToolExecutor(
        workspace=FixedWorkspace(tmp_path),
        patch_applier=GitPatchApplier(),
        test_runner=FakeTestRunner(TestRunResult(exit_code=0, stdout="", stderr="")),
        searcher=FakeSearcher(matches=[]),
        test_timeout_seconds=1,
    )
    args = ListFilesArgs(path=".").model_dump_json()
    result = executor.execute(ToolCall(name=ToolName.list_files, call_id="c2", arguments_json=args))
    assert "a.txt" in result.output_json
    assert "b.txt" in result.output_json


def test_search_repo_tool(tmp_path: Path) -> None:
    executor = CodexToolExecutor(
        workspace=FixedWorkspace(tmp_path),
        patch_applier=GitPatchApplier(),
        test_runner=FakeTestRunner(TestRunResult(exit_code=0, stdout="", stderr="")),
        searcher=FakeSearcher(matches=["file.py:1:needle"]),
        test_timeout_seconds=1,
    )
    args = SearchRepoArgs(query="needle").model_dump_json()
    result = executor.execute(ToolCall(name=ToolName.search_repo, call_id="c3", arguments_json=args))
    assert "needle" in result.output_json


def test_apply_patch_tool(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    target = tmp_path / "demo.txt"
    target.write_text("before\n", encoding="utf-8")
    original = tmp_path / "demo.txt.orig"
    original.write_text("before\n", encoding="utf-8")
    target.write_text("after\n", encoding="utf-8")
    diff = subprocess.run(
        [
            "diff",
            "-u",
            "--label",
            "demo.txt",
            "--label",
            "demo.txt",
            original.name,
            target.name,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    patch = diff.stdout
    target.write_text("before\n", encoding="utf-8")
    executor = CodexToolExecutor(
        workspace=FixedWorkspace(tmp_path),
        patch_applier=GitPatchApplier(),
        test_runner=FakeTestRunner(TestRunResult(exit_code=0, stdout="", stderr="")),
        searcher=FakeSearcher(matches=[]),
        test_timeout_seconds=1,
    )
    args = ApplyPatchArgs(diff=patch).model_dump_json()
    result = executor.execute(ToolCall(name=ToolName.apply_patch, call_id="c4", arguments_json=args))
    assert "true" in result.output_json
    assert target.read_text(encoding="utf-8") == "after\n"


def test_run_tests_tool(tmp_path: Path) -> None:
    executor = CodexToolExecutor(
        workspace=FixedWorkspace(tmp_path),
        patch_applier=GitPatchApplier(),
        test_runner=FakeTestRunner(TestRunResult(exit_code=5, stdout="", stderr="boom")),
        searcher=FakeSearcher(matches=[]),
        test_timeout_seconds=1,
    )
    args = RunTestsArgs(command="pytest").model_dump_json()
    result = executor.execute(ToolCall(name=ToolName.run_tests, call_id="c5", arguments_json=args))
    assert "\"exit_code\":5" in result.output_json
