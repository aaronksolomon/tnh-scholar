import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable

NowProvider = Callable[[], datetime]


@dataclass(frozen=True)
class CheckRecord:
    last_run_at: str | None
    last_success_at: str | None
    last_exit_code: int | None
    recommended_interval_days: int


CheckState = dict[str, CheckRecord]


@dataclass(frozen=True)
class HealthCheckPaths:
    repo_root: Path
    status_path: Path
    yt_dlp_script_path: Path


@dataclass(frozen=True)
class CheckOutcome:
    ran: bool
    success: bool
    summary: str


@dataclass(frozen=True)
class HealthCheckDefaults:
    recommended_interval_days: int = 10
    warn_after_days: int = 10
    fail_after_days: int = 30
    check_name: str = "yt_dlp_ops_check"


DEFAULTS = HealthCheckDefaults()


@dataclass
class UpdateHealthCheckService:
    paths: HealthCheckPaths
    runner: Callable[..., subprocess.CompletedProcess[str]]
    now_provider: NowProvider = lambda: datetime.now(UTC)

    def check_status(self, warn_after_days: int, fail_after_days: int) -> CheckOutcome:
        record = self._load_state().get(DEFAULTS.check_name)
        return self._build_status_outcome(record, warn_after_days, fail_after_days)

    def run_now(self, recommended_interval_days: int) -> CheckOutcome:
        state = self._load_state()
        defaults = HealthCheckDefaults(
            recommended_interval_days=recommended_interval_days,
        )
        return self._run_yt_dlp_ops_check(state, defaults)

    def _load_state(self) -> CheckState:
        if not self.paths.status_path.exists():
            return {}
        try:
            raw_state = json.loads(self.paths.status_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        raw_checks = raw_state.get("checks", {})
        return {
            name: self._build_record(raw_record)
            for name, raw_record in raw_checks.items()
            if isinstance(raw_record, dict)
        }

    def _build_record(self, raw_record: dict[str, object]) -> CheckRecord:
        def read_optional_str(key: str) -> str | None:
            value = raw_record.get(key)
            return value if isinstance(value, str) else None

        last_exit_code = raw_record.get("last_exit_code")
        return CheckRecord(
            last_run_at=read_optional_str("last_run_at"),
            last_success_at=read_optional_str("last_success_at"),
            last_exit_code=last_exit_code if isinstance(last_exit_code, int) else None,
            recommended_interval_days=self._read_recommended_interval(raw_record),
        )

    def _read_recommended_interval(self, raw_record: dict[str, object]) -> int:
        value = raw_record.get("recommended_interval_days")
        if isinstance(value, int) and value > 0:
            return value
        legacy_value = raw_record.get("stale_after_days")
        if isinstance(legacy_value, int) and legacy_value > 0:
            return legacy_value
        return DEFAULTS.recommended_interval_days

    def _build_status_outcome(
        self,
        record: CheckRecord | None,
        warn_after_days: int,
        fail_after_days: int,
    ) -> CheckOutcome:
        if record is None or record.last_run_at is None:
            summary = "yt-dlp health check status missing; run `make health-check`."
            print(summary)
            return CheckOutcome(ran=False, success=True, summary=summary)
        last_run_at = self._parse_timestamp(record.last_run_at)
        if last_run_at is None:
            summary = "yt-dlp health check status unreadable; run `make health-check`."
            print(summary)
            return CheckOutcome(ran=False, success=True, summary=summary)
        age = self.now_provider() - last_run_at
        if age >= timedelta(days=fail_after_days):
            summary = (
                "yt-dlp health check too old; failing until rerun. "
                f"last run: {record.last_run_at}, exit_code: {record.last_exit_code}."
            )
            print(summary)
            return CheckOutcome(ran=False, success=False, summary=summary)
        if age >= timedelta(days=warn_after_days):
            summary = (
                "yt-dlp health check stale; rerun soon with `make health-check`. "
                f"last run: {record.last_run_at}, exit_code: {record.last_exit_code}."
            )
            print(summary)
            return CheckOutcome(ran=False, success=True, summary=summary)
        summary = (
            f"yt-dlp health check fresh. last run: {record.last_run_at}, exit_code: {record.last_exit_code}."
        )
        print(summary)
        return CheckOutcome(ran=False, success=True, summary=summary)

    def _parse_timestamp(self, value: str) -> datetime | None:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

    def _run_yt_dlp_ops_check(
        self,
        state: CheckState,
        defaults: HealthCheckDefaults,
    ) -> CheckOutcome:
        print("Running yt-dlp live ops check.")
        result = self.runner(
            [sys.executable, str(self.paths.yt_dlp_script_path)],
            check=False,
        )
        updated_state = self._updated_state(state, defaults, result.returncode)
        self._write_state(updated_state)
        if result.returncode == 0:
            summary = "yt-dlp health check succeeded."
            print(summary)
            return CheckOutcome(ran=True, success=True, summary=summary)
        summary = "yt-dlp health check failed. See logs/yt_dlp_ops_check.log for details."
        print(summary)
        return CheckOutcome(ran=True, success=False, summary=summary)

    def _updated_state(
        self,
        state: CheckState,
        defaults: HealthCheckDefaults,
        exit_code: int,
    ) -> CheckState:
        now = self.now_provider().isoformat()
        previous = state.get(defaults.check_name)
        last_success_at = previous.last_success_at if previous is not None else None
        if exit_code == 0:
            last_success_at = now
        updated_checks = dict(state)
        updated_checks[defaults.check_name] = CheckRecord(
            last_run_at=now,
            last_success_at=last_success_at,
            last_exit_code=exit_code,
            recommended_interval_days=defaults.recommended_interval_days,
        )
        return updated_checks

    def _write_state(self, state: CheckState) -> None:
        self.paths.status_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "checks": {
                name: {
                    "last_run_at": record.last_run_at,
                    "last_success_at": record.last_success_at,
                    "last_exit_code": record.last_exit_code,
                    "recommended_interval_days": record.recommended_interval_days,
                }
                for name, record in state.items()
            }
        }
        self.paths.status_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _build_paths() -> HealthCheckPaths:
    repo_root = Path(__file__).resolve().parents[1]
    status_path = Path(
        os.environ.get(
            "TNH_HEALTH_STATUS_PATH",
            str(repo_root / "logs" / "update_health_check_status.json"),
        )
    )
    return HealthCheckPaths(
        repo_root=repo_root,
        status_path=status_path,
        yt_dlp_script_path=repo_root / "scripts" / "yt_dlp_ops_check.py",
    )


def _read_positive_int(env_name: str, default: int) -> int:
    raw_value = os.environ.get(env_name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or evaluate repo health checks.")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Execute the yt-dlp live ops check immediately and update status.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    defaults = HealthCheckDefaults(
        recommended_interval_days=_read_positive_int(
            "TNH_YT_DLP_RECOMMENDED_INTERVAL_DAYS",
            DEFAULTS.recommended_interval_days,
        ),
        warn_after_days=_read_positive_int(
            "TNH_HEALTH_WARN_AFTER_DAYS",
            DEFAULTS.warn_after_days,
        ),
        fail_after_days=_read_positive_int(
            "TNH_HEALTH_FAIL_AFTER_DAYS",
            DEFAULTS.fail_after_days,
        ),
    )
    service = UpdateHealthCheckService(
        paths=_build_paths(),
        runner=subprocess.run,
    )
    if args.run_now:
        outcome = service.run_now(
            recommended_interval_days=defaults.recommended_interval_days,
        )
    else:
        outcome = service.check_status(
            warn_after_days=defaults.warn_after_days,
            fail_after_days=defaults.fail_after_days,
        )
    raise SystemExit(0 if outcome.success else 1)


if __name__ == "__main__":
    main()
