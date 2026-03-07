"""Local RUN_VALIDATION executor with artifact capture."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.conductor_mvp.models import (
    BuiltinValidatorName,
    BuiltinValidatorSpec,
    HarnessReport,
    HarnessValidatorName,
    HarnessValidatorSpec,
    MechanicalOutcome,
    RunValidationStep,
    ValidationRunResult,
    ValidatorExecutionSpec,
)
from tnh_scholar.agent_orchestration.conductor_mvp.protocols import (
    ValidationRunnerProtocol,
    ValidatorResolverProtocol,
)


class BuiltinCommandEntry(BaseModel):
    """Builtin validator command mapping entry."""

    name: BuiltinValidatorName
    command: tuple[str, ...] = Field(default_factory=tuple)


@dataclass(frozen=True)
class StaticValidatorResolver(ValidatorResolverProtocol):
    """Resolve trusted validator refs from code-owned mappings."""

    entries: list[BuiltinCommandEntry]
    harness_script_name: str = "generated_harness.py"
    harness_report_name: str = "harness_report.json"

    def resolve(
        self,
        validator: BuiltinValidatorSpec | HarnessValidatorSpec,
        run_dir: Path,
    ) -> ValidatorExecutionSpec:
        """Resolve validator into a trusted execution spec."""
        if isinstance(validator, BuiltinValidatorSpec):
            return self._resolve_builtin(validator, run_dir)
        return self._resolve_harness(validator, run_dir)

    def _resolve_builtin(
        self,
        validator: BuiltinValidatorSpec,
        run_dir: Path,
    ) -> ValidatorExecutionSpec:
        for entry in self.entries:
            if entry.name == validator.name:
                return ValidatorExecutionSpec(command=entry.command, cwd=run_dir)
        raise ValueError(f"Unknown builtin validator: {validator.name.value}")

    def _resolve_harness(
        self,
        validator: HarnessValidatorSpec,
        run_dir: Path,
    ) -> ValidatorExecutionSpec:
        match validator.name:
            case HarnessValidatorName.generated_harness:
                return ValidatorExecutionSpec(
                    command=(
                        sys.executable,
                        str(run_dir / self.harness_script_name),
                        "--report",
                        self.harness_report_name,
                    ),
                    cwd=run_dir,
                    artifacts=tuple(validator.artifacts),
                    timeout_seconds=validator.timeout_seconds,
                )
        raise ValueError(f"Unsupported harness validator: {validator.name.value}")


@dataclass(frozen=True)
class LocalValidationRunner(ValidationRunnerProtocol):
    """Run validators via subprocess in the local worktree."""

    validator_resolver: ValidatorResolverProtocol
    artifacts_subdir: str = "validation_artifacts"

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
        validator: BuiltinValidatorSpec | HarnessValidatorSpec,
        run_dir: Path,
    ) -> ValidationRunResult:
        execution = self.validator_resolver.resolve(validator, run_dir)
        return self._run_command(
            execution.command,
            execution.cwd,
            run_dir,
            execution.timeout_seconds,
            execution.artifacts,
        )

    def _run_command(
        self,
        command: tuple[str, ...],
        cwd: Path,
        run_dir: Path,
        timeout_seconds: int | None,
        artifacts: tuple[str, ...],
    ) -> ValidationRunResult:
        try:
            self._validate_command(command, cwd)
            process = subprocess.run(
                list(command),
                cwd=cwd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            self._capture_artifacts(cwd, run_dir, artifacts)
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

    def _validate_command(self, command: tuple[str, ...], cwd: Path) -> None:
        if not command:
            raise ValueError("Validation command must not be empty.")
        executable = Path(command[0])
        if executable.is_absolute():
            if not executable.exists():
                raise ValueError(f"Validation executable does not exist: {executable}")
            return
        if executable.parent != Path("."):
            candidate = (cwd / executable).resolve()
            if not candidate.exists():
                raise ValueError(f"Validation executable does not exist: {candidate}")

    def _capture_artifacts(self, cwd: Path, run_dir: Path, globs: tuple[str, ...]) -> None:
        artifacts_root = run_dir / self.artifacts_subdir
        for pattern in globs:
            for path in cwd.glob(pattern):
                if path.is_file():
                    relative_path = path.relative_to(cwd)
                    destination = artifacts_root / relative_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, destination)

    def _load_harness_report(self, cwd: Path) -> HarnessReport | None:
        path = cwd / "harness_report.json"
        return self._parse_harness_report(path) if path.exists() else None

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
        return current if new_value is None else new_value
