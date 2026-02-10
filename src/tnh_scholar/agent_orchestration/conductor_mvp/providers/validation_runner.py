"""Local RUN_VALIDATION executor with artifact capture."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.conductor_mvp.models import (
    BuiltinValidatorSpec,
    HarnessReport,
    MechanicalOutcome,
    RunValidationStep,
    ScriptValidatorSpec,
    ValidationRunResult,
)
from tnh_scholar.agent_orchestration.conductor_mvp.protocols import (
    BuiltinValidatorResolverProtocol,
    ValidationRunnerProtocol,
)


class BuiltinCommandEntry(BaseModel):
    """Builtin validator command mapping entry."""

    name: str
    command: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class StaticBuiltinValidatorResolver(BuiltinValidatorResolverProtocol):
    """Resolve builtin validator commands from a static mapping."""

    entries: list[BuiltinCommandEntry]

    def resolve(self, validator: BuiltinValidatorSpec) -> list[str]:
        """Resolve command for builtin validator name."""
        for entry in self.entries:
            if entry.name == validator.name:
                return entry.command
        raise ValueError(f"Unknown builtin validator: {validator.name}")


@dataclass(frozen=True)
class LocalValidationRunner(ValidationRunnerProtocol):
    """Run validators via subprocess in the local worktree."""

    builtin_resolver: BuiltinValidatorResolverProtocol

    def run(self, step: RunValidationStep, run_dir: Path) -> ValidationRunResult:
        """Execute all validators and aggregate outcome/report."""
        outcome = MechanicalOutcome.completed
        latest_report = None
        for validator in step.run:
            result = self._run_one(validator, run_dir)
            outcome = self._merge_outcome(outcome, result.outcome)
            latest_report = self._prefer_report(latest_report, result.harness_report)
        return ValidationRunResult(outcome=outcome, harness_report=latest_report)

    def _run_one(
        self,
        validator: BuiltinValidatorSpec | ScriptValidatorSpec,
        run_dir: Path,
    ) -> ValidationRunResult:
        if isinstance(validator, BuiltinValidatorSpec):
            command = self.builtin_resolver.resolve(validator)
            return self._run_command(command, run_dir, None, [])
        return self._run_command(
            [str(validator.entrypoint), *validator.args],
            validator.cwd or run_dir,
            validator.timeout_seconds,
            validator.artifacts,
        )

    def _run_command(
        self,
        command: list[str],
        cwd: Path,
        timeout_seconds: int | None,
        artifacts: list[str],
    ) -> ValidationRunResult:
        try:
            process = subprocess.run(
                command,
                cwd=cwd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            self._capture_artifacts(cwd, artifacts)
            harness_report = self._load_harness_report(cwd)
            if process.returncode == 0:
                return ValidationRunResult(
                    outcome=MechanicalOutcome.completed,
                    harness_report=harness_report,
                )
            return ValidationRunResult(
                outcome=MechanicalOutcome.error,
                harness_report=harness_report,
            )
        except subprocess.TimeoutExpired:
            return ValidationRunResult(outcome=MechanicalOutcome.killed_timeout)

    def _capture_artifacts(self, cwd: Path, globs: list[str]) -> None:
        for pattern in globs:
            for path in cwd.glob(pattern):
                if path.is_file():
                    relative_path = path.relative_to(cwd)
                    destination = cwd / relative_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if path != destination:
                        shutil.copy2(path, destination)

    def _load_harness_report(self, cwd: Path) -> HarnessReport | None:
        path = cwd / "harness_report.json"
        if not path.exists():
            return None
        return self._parse_harness_report(path)

    def _parse_harness_report(self, path: Path) -> HarnessReport | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return HarnessReport.model_validate(payload)

    def _merge_outcome(
        self,
        current: MechanicalOutcome,
        new_value: MechanicalOutcome,
    ) -> MechanicalOutcome:
        if current == MechanicalOutcome.killed_timeout:
            return current
        if new_value == MechanicalOutcome.killed_timeout:
            return new_value
        if current == MechanicalOutcome.error or new_value == MechanicalOutcome.error:
            return MechanicalOutcome.error
        return current

    def _prefer_report(
        self,
        current: HarnessReport | None,
        new_value: HarnessReport | None,
    ) -> HarnessReport | None:
        if new_value is None:
            return current
        return new_value
