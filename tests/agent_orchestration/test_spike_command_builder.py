"""Tests for the spike command builder."""

from pathlib import Path

import pytest

from tnh_scholar.agent_orchestration.spike.models import SpikeParams
from tnh_scholar.agent_orchestration.spike.providers.command_builder import AgentCommandBuilder


def test_build_claude_command() -> None:
    builder = AgentCommandBuilder()
    params = SpikeParams(agent="claude-code", task="List files")
    command = builder.build(params)
    assert command == ["claude", "--print", "List files"]


def test_build_codex_command() -> None:
    builder = AgentCommandBuilder()
    response_path = Path("/tmp/response.txt")
    params = SpikeParams(agent="codex", task="List files", response_path=response_path)
    command = builder.build(params)
    assert command == [
        "codex",
        "exec",
        "--json",
        "--output-last-message",
        str(response_path),
        "--full-auto",
        "-m",
        "gpt-5.2-codex",
        "List files",
    ]


def test_build_codex_command_requires_response_path() -> None:
    builder = AgentCommandBuilder()
    params = SpikeParams(agent="codex", task="List files")
    with pytest.raises(ValueError, match="response_path is required"):
        builder.build(params)
