import importlib.util
import subprocess
import sys
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "update_health_check.py"
    spec = importlib.util.spec_from_file_location("update_health_check", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


health_check = _load_module()


def _write_status(status_path: Path, last_run_at: str, exit_code: int) -> None:
    status_path.write_text(
        f"""
        {{
          "checks": {{
            "yt_dlp_ops_check": {{
              "last_exit_code": {exit_code},
              "last_run_at": "{last_run_at}",
              "last_success_at": "{last_run_at}",
              "recommended_interval_days": 10
            }}
          }}
        }}
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def test_check_status_succeeds_when_fresh(tmp_path: Path) -> None:
    status_path = tmp_path / "status.json"
    _write_status(status_path, "2026-04-21T12:00:00+00:00", 0)
    paths = health_check.HealthCheckPaths(
        repo_root=tmp_path,
        status_path=status_path,
        yt_dlp_script_path=tmp_path / "scripts" / "yt_dlp_ops_check.py",
    )
    service = health_check.UpdateHealthCheckService(
        paths=paths,
        runner=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")),
    )

    outcome = service.check_status(warn_after_days=10, fail_after_days=30)

    assert outcome.ran is False
    assert outcome.success is True
    assert "fresh" in outcome.summary


def test_check_status_warns_when_stale_but_not_expired(tmp_path: Path) -> None:
    status_path = tmp_path / "status.json"
    _write_status(status_path, "2026-04-05T12:00:00+00:00", 0)
    paths = health_check.HealthCheckPaths(
        repo_root=tmp_path,
        status_path=status_path,
        yt_dlp_script_path=tmp_path / "scripts" / "yt_dlp_ops_check.py",
    )
    service = health_check.UpdateHealthCheckService(
        paths=paths,
        runner=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")),
    )

    outcome = service.check_status(warn_after_days=10, fail_after_days=30)

    assert outcome.ran is False
    assert outcome.success is True
    assert "stale" in outcome.summary


def test_check_status_fails_when_too_old(tmp_path: Path) -> None:
    status_path = tmp_path / "status.json"
    _write_status(status_path, "2026-03-01T12:00:00+00:00", 0)
    paths = health_check.HealthCheckPaths(
        repo_root=tmp_path,
        status_path=status_path,
        yt_dlp_script_path=tmp_path / "scripts" / "yt_dlp_ops_check.py",
    )
    service = health_check.UpdateHealthCheckService(
        paths=paths,
        runner=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")),
    )

    outcome = service.check_status(warn_after_days=10, fail_after_days=30)

    assert outcome.ran is False
    assert outcome.success is False
    assert "too old" in outcome.summary


def test_check_status_warns_when_status_missing(tmp_path: Path) -> None:
    paths = health_check.HealthCheckPaths(
        repo_root=tmp_path,
        status_path=tmp_path / "status.json",
        yt_dlp_script_path=tmp_path / "scripts" / "yt_dlp_ops_check.py",
    )
    service = health_check.UpdateHealthCheckService(
        paths=paths,
        runner=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("runner should not be called")),
    )

    outcome = service.check_status(warn_after_days=10, fail_after_days=30)

    assert outcome.ran is False
    assert outcome.success is True
    assert "status missing" in outcome.summary


def test_run_now_executes_and_persists_success(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(cmd, check=False, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    paths = health_check.HealthCheckPaths(
        repo_root=tmp_path,
        status_path=tmp_path / "status.json",
        yt_dlp_script_path=tmp_path / "scripts" / "yt_dlp_ops_check.py",
    )
    service = health_check.UpdateHealthCheckService(paths=paths, runner=runner)

    outcome = service.run_now(recommended_interval_days=10)

    assert outcome.ran is True
    assert outcome.success is True
    assert calls == [[sys.executable, str(paths.yt_dlp_script_path)]]
    saved = paths.status_path.read_text(encoding="utf-8")
    assert '"last_exit_code": 0' in saved
    assert '"recommended_interval_days": 10' in saved


def test_run_now_executes_and_persists_failure(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(cmd, check=False, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=1)

    paths = health_check.HealthCheckPaths(
        repo_root=tmp_path,
        status_path=tmp_path / "status.json",
        yt_dlp_script_path=tmp_path / "scripts" / "yt_dlp_ops_check.py",
    )
    service = health_check.UpdateHealthCheckService(paths=paths, runner=runner)

    outcome = service.run_now(recommended_interval_days=10)

    assert outcome.ran is True
    assert outcome.success is False
    assert calls == [[sys.executable, str(paths.yt_dlp_script_path)]]
    saved = paths.status_path.read_text(encoding="utf-8")
    assert '"last_exit_code": 1' in saved
