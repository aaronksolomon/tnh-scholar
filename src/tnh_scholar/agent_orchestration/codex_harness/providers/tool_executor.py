"""Tool execution provider for Codex harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from tnh_scholar.agent_orchestration.codex_harness.protocols import (
    PatchApplierProtocol,
    SearcherProtocol,
    TestRunnerProtocol,
    ToolExecutorProtocol,
    WorkspaceLocatorProtocol,
)
from tnh_scholar.agent_orchestration.codex_harness.tools import (
    ApplyPatchArgs,
    ApplyPatchResult,
    ListFilesArgs,
    ListFilesResult,
    ReadFileArgs,
    ReadFileResult,
    RunTestsArgs,
    RunTestsResult,
    SearchRepoArgs,
    SearchRepoResult,
    ToolCall,
    ToolName,
    ToolResult,
)


@dataclass(frozen=True)
class CodexToolExecutor(ToolExecutorProtocol):
    """Execute Codex tool calls against the repo."""

    workspace: WorkspaceLocatorProtocol
    patch_applier: PatchApplierProtocol
    test_runner: TestRunnerProtocol
    searcher: SearcherProtocol
    test_timeout_seconds: int

    def execute(self, call: ToolCall) -> ToolResult:
        handler = self._handler_for(call.name)
        output = handler(call)
        return ToolResult(name=call.name, call_id=call.call_id, output_json=output)

    def _handler_for(self, name: ToolName):
        if name == ToolName.read_file:
            return self._handle_read_file
        if name == ToolName.list_files:
            return self._handle_list_files
        if name == ToolName.search_repo:
            return self._handle_search_repo
        if name == ToolName.apply_patch:
            return self._handle_apply_patch
        if name == ToolName.run_tests:
            return self._handle_run_tests
        raise ValueError(f"Unsupported tool: {name}")

    def _handle_read_file(self, call: ToolCall) -> str:
        args = self._parse_args(ReadFileArgs, call.arguments_json)
        path = self._resolve_path(args.path)
        try:
            content = path.read_text(encoding="utf-8")
            payload = ReadFileResult(path=str(path), content=content)
        except FileNotFoundError:
            payload = ReadFileResult(path=str(path), content="", error="File not found")
        return payload.model_dump_json()

    def _handle_list_files(self, call: ToolCall) -> str:
        args = self._parse_args(ListFilesArgs, call.arguments_json)
        path = self._resolve_path(args.path)
        try:
            entries = sorted([entry.name for entry in path.iterdir()])
            payload = ListFilesResult(path=str(path), entries=entries)
        except FileNotFoundError:
            payload = ListFilesResult(path=str(path), entries=[], error="Path not found")
        return payload.model_dump_json()

    def _handle_search_repo(self, call: ToolCall) -> str:
        args = self._parse_args(SearchRepoArgs, call.arguments_json)
        root = self.workspace.repo_root()
        try:
            matches = self.searcher.search(args.query, root)
            payload = SearchRepoResult(query=args.query, matches=matches)
        except RuntimeError as exc:
            payload = SearchRepoResult(query=args.query, matches=[], error=str(exc))
        return payload.model_dump_json()

    def _handle_apply_patch(self, call: ToolCall) -> str:
        args = self._parse_args(ApplyPatchArgs, call.arguments_json)
        result = self.patch_applier.apply(args.diff)
        payload = ApplyPatchResult(
            applied=result.applied,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        return payload.model_dump_json()

    def _handle_run_tests(self, call: ToolCall) -> str:
        args = self._parse_args(RunTestsArgs, call.arguments_json)
        result = self.test_runner.run(args.command, timeout_seconds=self.test_timeout_seconds)
        payload = RunTestsResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        return payload.model_dump_json()

    def _parse_args(self, model, raw: str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Tool arguments are not valid JSON") from exc
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise ValueError("Tool arguments did not match schema") from exc

    def _resolve_path(self, raw_path: str) -> Path:
        root = self.workspace.repo_root()
        path = (root / raw_path).resolve()
        if not str(path).startswith(str(root)):
            raise ValueError("Path escapes repo root")
        return path
