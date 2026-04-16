"""Tests for maintained runner adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from tnh_scholar.agent_orchestration.execution import (
    ExplicitEnvironmentPolicy,
    SubprocessExecutionService,
)
from tnh_scholar.agent_orchestration.execution_policy import (
    ApprovalPosture,
    ExecutionPosture,
    NetworkPosture,
    RequestedExecutionPolicy,
)
from tnh_scholar.agent_orchestration.runners import (
    DelegatingRunnerService,
    RunnerInvocationMode,
    RunnerTaskRequest,
    RunnerTermination,
)
from tnh_scholar.agent_orchestration.runners.adapters import (
    ClaudeCliRunnerAdapter,
    CodexCliRunnerAdapter,
)
from tnh_scholar.agent_orchestration.runners.adapters.codex_cli import CodexCliInvocationMapper
from tnh_scholar.agent_orchestration.shared_enums import AgentFamily


def test_claude_cli_adapter_normalizes_stdout_to_runner_artifacts(tmp_path: Path) -> None:
    executable = tmp_path / "claude"
    executable.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' "
        "'{\"type\":\"start\"}' "
        "'{\"type\":\"assistant\",\"text\":\"done from claude\"}'\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    adapter = ClaudeCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    result = adapter.run(
        RunnerTaskRequest(
            agent_family=AgentFamily.claude_cli,
            rendered_task_text="say hi",
            working_directory=tmp_path,
            requested_policy=RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.workspace_write,
            ),
        )
    )

    assert result.termination == RunnerTermination.completed
    assert result.transcript is not None
    assert result.final_response is not None
    assert result.final_response.content.strip() == "done from claude"
    assert result.metadata is not None
    assert result.metadata.invocation_mode == RunnerInvocationMode.claude_print
    assert result.metadata.command[:5] == (
        str(executable),
        "--print",
        "--output-format",
        "stream-json",
        "--permission-mode",
    )


def test_claude_cli_adapter_ignores_non_assistant_text_when_extracting_final_response(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "claude"
    executable.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' "
        "'{\"type\":\"tool_result\",\"text\":\"tool chatter\"}' "
        "'{\"type\":\"assistant\",\"text\":\"true final response\"}'\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    adapter = ClaudeCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    result = adapter.run(
        RunnerTaskRequest(
            agent_family=AgentFamily.claude_cli,
            rendered_task_text="say hi",
            working_directory=tmp_path,
            requested_policy=RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.workspace_write,
            ),
        )
    )

    assert result.final_response is not None
    assert result.final_response.content.strip() == "true final response"


def test_claude_cli_adapter_rejects_read_only_policy(tmp_path: Path) -> None:
    executable = tmp_path / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    adapter = ClaudeCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    with pytest.raises(ValueError, match="read_only"):
        adapter.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.claude_cli,
                rendered_task_text="say hi",
                working_directory=tmp_path,
                requested_policy=RequestedExecutionPolicy(
                    execution_posture=ExecutionPosture.read_only,
                ),
            )
        )


def test_claude_cli_adapter_rejects_unsupported_network_policy(tmp_path: Path) -> None:
    executable = tmp_path / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    adapter = ClaudeCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    with pytest.raises(ValueError, match="network posture"):
        adapter.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.claude_cli,
                rendered_task_text="say hi",
                working_directory=tmp_path,
                requested_policy=RequestedExecutionPolicy(
                    execution_posture=ExecutionPosture.workspace_write,
                    network_posture=NetworkPosture.deny,
                ),
            )
        )


def test_claude_cli_adapter_rejects_allowed_paths_policy(tmp_path: Path) -> None:
    executable = tmp_path / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    adapter = ClaudeCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    with pytest.raises(ValueError, match="allowed_paths"):
        adapter.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.claude_cli,
                rendered_task_text="say hi",
                working_directory=tmp_path,
                requested_policy=RequestedExecutionPolicy(
                    execution_posture=ExecutionPosture.workspace_write,
                    allowed_paths=(tmp_path / "some_path",),
                ),
            )
        )


def test_claude_cli_adapter_rejects_forbidden_paths_policy(tmp_path: Path) -> None:
    executable = tmp_path / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    adapter = ClaudeCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    with pytest.raises(ValueError, match="forbidden_paths"):
        adapter.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.claude_cli,
                rendered_task_text="say hi",
                working_directory=tmp_path,
                requested_policy=RequestedExecutionPolicy(
                    execution_posture=ExecutionPosture.workspace_write,
                    forbidden_paths=(tmp_path / "some_path",),
                ),
            )
        )


def test_claude_cli_adapter_rejects_forbidden_operations_policy(tmp_path: Path) -> None:
    executable = tmp_path / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    adapter = ClaudeCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    with pytest.raises(ValueError, match="forbidden_operations"):
        adapter.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.claude_cli,
                rendered_task_text="say hi",
                working_directory=tmp_path,
                requested_policy=RequestedExecutionPolicy(
                    execution_posture=ExecutionPosture.workspace_write,
                    forbidden_operations=("write",),
                ),
            )
        )


def test_runner_adapter_rejects_non_executable_configured_path(tmp_path: Path) -> None:
    executable = tmp_path / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    adapter = ClaudeCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    with pytest.raises(OSError, match="not executable"):
        adapter.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.claude_cli,
                rendered_task_text="say hi",
                working_directory=tmp_path,
            )
        )


def test_codex_cli_adapter_reads_final_response_and_maps_workspace_write(tmp_path: Path) -> None:
    executable = tmp_path / "codex"
    executable.write_text(
        "#!/bin/sh\n"
        "response=''\n"
        "sandbox=''\n"
        "while [ $# -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --output-last-message)\n"
        "      response=\"$2\"\n"
        "      shift 2\n"
        "      ;;\n"
        "    --sandbox)\n"
        "      sandbox=\"$2\"\n"
        "      shift 2\n"
        "      ;;\n"
        "    *)\n"
        "      shift\n"
        "      ;;\n"
        "  esac\n"
        "done\n"
        "printf 'codex final\\n' > \"$response\"\n"
        "printf '%s\\n' "
        "'{\"type\":\"thread.started\"}' "
        "\"{\\\"type\\\":\\\"item.completed\\\",\\\"item\\\":{\\\"type\\\":\\\"agent_message\\\",\\\"text\\\":\\\"sandbox:$sandbox\\\"}}\"\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    adapter = CodexCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    result = adapter.run(
        RunnerTaskRequest(
            agent_family=AgentFamily.codex_cli,
            rendered_task_text="do work",
            working_directory=tmp_path,
            requested_policy=RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.workspace_write,
            ),
        )
    )

    assert result.termination == RunnerTermination.completed
    assert result.transcript is not None
    assert result.final_response is not None
    assert result.final_response.content.strip() == "codex final"
    assert result.metadata is not None
    assert "--ephemeral" in result.metadata.command
    assert "--sandbox" in result.metadata.command
    assert "workspace-write" in result.metadata.command
    assert "-m" not in result.metadata.command
    response_flag_index = result.metadata.command.index("--output-last-message")
    response_path = Path(result.metadata.command[response_flag_index + 1])
    assert not response_path.is_relative_to(tmp_path)
    assert result.metadata.invocation_mode == RunnerInvocationMode.codex_exec


def test_codex_cli_mapper_builds_explicit_user_like_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", "/Users/tester")
    monkeypatch.setenv("PATH", "/opt/homebrew/bin:/usr/bin:/bin")
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    monkeypatch.setenv("TMPDIR", "/tmp/tester")
    monkeypatch.setenv("USER", "tester")
    monkeypatch.setenv("LOGNAME", "tester")
    monkeypatch.setenv("SSH_AUTH_SOCK", "/tmp/ssh.sock")
    monkeypatch.setenv("CODEX_CI", "1")
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-123")
    monkeypatch.setenv("VSCODE_PID", "999")
    monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
    mapper = CodexCliInvocationMapper(executable=tmp_path / "codex")

    execution_request = mapper.map(
        RunnerTaskRequest(
            agent_family=AgentFamily.codex_cli,
            rendered_task_text="do work",
            working_directory=tmp_path,
            requested_policy=RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.workspace_write,
            ),
        ),
        tmp_path / "response.txt",
    )

    policy = execution_request.environment_policy
    assert isinstance(policy, ExplicitEnvironmentPolicy)
    assert policy.values["HOME"] == "/Users/tester"
    assert policy.values["PATH"] == "/opt/homebrew/bin:/usr/bin:/bin"
    assert policy.values["TERM"] == "xterm-256color"
    assert policy.values["PWD"] == str(tmp_path)
    assert policy.values["TERM_PROGRAM"] == "Apple_Terminal"
    assert "CODEX_CI" not in policy.values
    assert "CODEX_THREAD_ID" not in policy.values
    assert "VSCODE_PID" not in policy.values


def test_codex_cli_mapper_normalizes_dumb_term_and_falls_back_for_missing_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TMPDIR", raising=False)
    monkeypatch.delenv("LANG", raising=False)
    monkeypatch.delenv("SHELL", raising=False)
    monkeypatch.setenv("HOME", "/Users/tester")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setenv("TERM", "dumb")
    mapper = CodexCliInvocationMapper(executable=tmp_path / "codex")

    execution_request = mapper.map(
        RunnerTaskRequest(
            agent_family=AgentFamily.codex_cli,
            rendered_task_text="do work",
            working_directory=tmp_path,
        ),
        tmp_path / "response.txt",
    )

    policy = execution_request.environment_policy
    assert isinstance(policy, ExplicitEnvironmentPolicy)
    assert policy.values["TERM"] == "xterm-256color"
    assert policy.values["LANG"] == "en_US.UTF-8"
    assert policy.values["SHELL"] == "/bin/zsh"
    assert policy.values["TMPDIR"] == "/tmp"


def test_codex_cli_adapter_includes_model_when_configured(tmp_path: Path) -> None:
    executable = tmp_path / "codex"
    executable.write_text(
        "#!/bin/sh\n"
        "response=''\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--output-last-message\" ]; then\n"
        "    response=\"$2\"\n"
        "    shift 2\n"
        "  else\n"
        "    shift\n"
        "  fi\n"
        "done\n"
        "printf 'codex final\\n' > \"$response\"\n"
        "printf '%s\\n' '{\"type\":\"thread.started\"}'\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    adapter = CodexCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
        model_name="gpt-test",
    )

    result = adapter.run(
        RunnerTaskRequest(
            agent_family=AgentFamily.codex_cli,
            rendered_task_text="do work",
            working_directory=tmp_path,
        )
    )

    assert result.termination == RunnerTermination.completed
    assert result.metadata is not None
    assert "-m" in result.metadata.command
    assert "gpt-test" in result.metadata.command


def test_codex_cli_adapter_rejects_bounded_auto_approve(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    adapter = CodexCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    with pytest.raises(ValueError, match="bounded_auto_approve"):
        adapter.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.codex_cli,
                rendered_task_text="do work",
                working_directory=tmp_path,
                requested_policy=RequestedExecutionPolicy(
                    execution_posture=ExecutionPosture.workspace_write,
                    approval_posture=ApprovalPosture.bounded_auto_approve,
                ),
            )
        )


def test_codex_cli_adapter_returns_error_when_final_response_is_missing(tmp_path: Path) -> None:
    executable = tmp_path / "codex"
    executable.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' '{\"type\":\"thread.started\"}'\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    adapter = CodexCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    result = adapter.run(
        RunnerTaskRequest(
            agent_family=AgentFamily.codex_cli,
            rendered_task_text="do work",
            working_directory=tmp_path,
            requested_policy=RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.read_only,
            ),
        )
    )

    assert result.termination == RunnerTermination.error
    assert result.transcript is not None
    assert result.final_response is None


def test_codex_cli_adapter_rejects_unsupported_network_policy(tmp_path: Path) -> None:
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    adapter = CodexCliRunnerAdapter(
        execution_service=SubprocessExecutionService(),
        executable=executable,
    )

    with pytest.raises(ValueError, match="network posture"):
        adapter.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.codex_cli,
                rendered_task_text="do work",
                working_directory=tmp_path,
                requested_policy=RequestedExecutionPolicy(
                    execution_posture=ExecutionPosture.read_only,
                    network_posture=NetworkPosture.deny,
                ),
            )
        )


def test_delegating_runner_service_routes_to_matching_adapter(tmp_path: Path) -> None:
    claude = tmp_path / "claude"
    claude.write_text("#!/bin/sh\nprintf '%s\\n' '{\"text\":\"claude\"}'\n", encoding="utf-8")
    claude.chmod(0o755)
    codex = tmp_path / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--output-last-message\" ]; then\n"
        "    printf 'codex\\n' > \"$2\"\n"
        "    shift 2\n"
        "  else\n"
        "    shift\n"
        "  fi\n"
        "done\n"
        "printf '%s\\n' '{\"type\":\"thread.started\"}'\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    service = DelegatingRunnerService(
        adapters=(
            ClaudeCliRunnerAdapter(
                execution_service=SubprocessExecutionService(),
                executable=claude,
            ),
            CodexCliRunnerAdapter(
                execution_service=SubprocessExecutionService(),
                executable=codex,
            ),
        )
    )

    result = service.run(
        RunnerTaskRequest(
            agent_family=AgentFamily.codex_cli,
            rendered_task_text="do work",
            working_directory=tmp_path,
        )
    )

    assert result.metadata is not None
    assert result.metadata.agent_family == AgentFamily.codex_cli


def test_delegating_runner_service_raises_for_unknown_family(tmp_path: Path) -> None:
    claude = tmp_path / "claude"
    claude.write_text(
        "#!/bin/sh\nprintf '%s\\n' '{\"type\":\"assistant\",\"text\":\"ok\"}'\n",
        encoding="utf-8",
    )
    claude.chmod(0o755)
    service = DelegatingRunnerService(
        adapters=(
            ClaudeCliRunnerAdapter(
                execution_service=SubprocessExecutionService(),
                executable=claude,
            ),
        )
    )

    with pytest.raises(ValueError, match="codex_cli"):
        service.run(
            RunnerTaskRequest(
                agent_family=AgentFamily.codex_cli,
                rendered_task_text="do work",
                working_directory=tmp_path,
            )
        )
