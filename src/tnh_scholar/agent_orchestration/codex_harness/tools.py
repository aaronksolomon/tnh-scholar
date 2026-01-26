"""Tooling definitions for Codex harness."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


class ToolName(str, Enum):
    read_file = "read_file"
    list_files = "list_files"
    search_repo = "search_repo"
    apply_patch = "apply_patch"
    run_tests = "run_tests"


class ToolCall(BaseModel):
    """Parsed tool call from Codex."""

    name: ToolName
    call_id: str
    arguments_json: str


class ToolResult(BaseModel):
    """Tool execution result."""

    name: ToolName
    call_id: str
    output_json: str


class ToolDefinition(BaseModel):
    """Definition for a callable tool."""

    name: ToolName
    description: str
    parameters_schema: dict[str, object]


class ReadFileArgs(BaseModel):
    path: str


class ListFilesArgs(BaseModel):
    path: str


class SearchRepoArgs(BaseModel):
    query: str


class ApplyPatchArgs(BaseModel):
    diff: str


class RunTestsArgs(BaseModel):
    command: str


class ReadFileResult(BaseModel):
    path: str
    content: str
    error: str | None = None


class ListFilesResult(BaseModel):
    path: str
    entries: list[str] = Field(default_factory=list)
    error: str | None = None


class SearchRepoResult(BaseModel):
    query: str
    matches: list[str] = Field(default_factory=list)
    error: str | None = None


class ApplyPatchResult(BaseModel):
    applied: bool
    stdout: str
    stderr: str


class RunTestsResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ToolSchemaFactory:
    """Build JSON schema definitions for tools."""

    def _string_arg_schema(self, key: str) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {key: {"type": "string"}},
            "required": [key],
            "additionalProperties": False,
        }

    def read_file(self) -> ToolDefinition:
        return ToolDefinition(
            name=ToolName.read_file,
            description="Read a file from the repository.",
            parameters_schema=self._string_arg_schema("path"),
        )

    def list_files(self) -> ToolDefinition:
        return ToolDefinition(
            name=ToolName.list_files,
            description="List entries in a directory.",
            parameters_schema=self._string_arg_schema("path"),
        )

    def search_repo(self) -> ToolDefinition:
        return ToolDefinition(
            name=ToolName.search_repo,
            description="Search the repository for a query string.",
            parameters_schema=self._string_arg_schema("query"),
        )

    def apply_patch(self) -> ToolDefinition:
        return ToolDefinition(
            name=ToolName.apply_patch,
            description="Apply a unified diff patch to the repository.",
            parameters_schema=self._string_arg_schema("diff"),
        )

    def run_tests(self) -> ToolDefinition:
        return ToolDefinition(
            name=ToolName.run_tests,
            description="Run a test command in the repository.",
            parameters_schema=self._string_arg_schema("command"),
        )

    def all_definitions(self) -> list[ToolDefinition]:
        return [
            self.read_file(),
            self.list_files(),
            self.search_repo(),
            self.apply_patch(),
            self.run_tests(),
        ]
