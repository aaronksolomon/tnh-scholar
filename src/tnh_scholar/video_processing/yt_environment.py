import importlib.util
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.video_processing.yt_preflight_report import (
    YTPreflightItem,
    YTPreflightReport,
)


@dataclass(frozen=True)
class YTDLPEnvironmentReport:
    """Report describing preflight environment concerns for yt-dlp."""

    warnings: tuple[str, ...]

    def has_warnings(self) -> bool:
        """Return True when warnings are present."""
        return bool(self.warnings)


class YTDLPEnvironmentInspector:
    """Preflight checks for yt-dlp runtime dependencies."""

    def inspect(self) -> YTDLPEnvironmentReport:
        """Inspect the environment for common yt-dlp runtime gaps."""
        warnings = []

        if not self._has_js_runtime():
            warnings.append(
                "yt-dlp JS runtime missing. Install deno or node and configure --js-runtimes."
            )

        if not self._has_impersonation_runtime():
            warnings.append(
                "yt-dlp impersonation runtime missing. Install curl_cffi if impersonation warnings appear."
            )

        return YTDLPEnvironmentReport(warnings=tuple(warnings))

    def inspect_report(self) -> YTPreflightReport:
        """Return a structured preflight report for user-facing output."""
        items = self._build_preflight_items()
        return YTPreflightReport(items=tuple(items))

    def _build_preflight_items(self) -> list[YTPreflightItem]:
        items: list[YTPreflightItem] = []
        if not self._has_js_runtime():
            items.append(self._missing_js_runtime_item())
        elif not self._has_remote_components_config():
            items.append(self._missing_remote_components_item())
        if not self._has_impersonation_runtime():
            items.append(self._missing_impersonation_runtime_item())
        return items

    def _missing_js_runtime_item(self) -> YTPreflightItem:
        return YTPreflightItem(
            code="missing_js_runtime",
            message="yt-dlp JS runtime missing. Install deno or node and configure --js-runtimes.",
        )

    def _missing_impersonation_runtime_item(self) -> YTPreflightItem:
        return YTPreflightItem(
            code="missing_impersonation_runtime",
            message=(
                "yt-dlp impersonation runtime missing. Install curl_cffi if impersonation warnings appear."
            ),
        )

    def _missing_remote_components_item(self) -> YTPreflightItem:
        return YTPreflightItem(
            code="missing_remote_components",
            message=(
                "yt-dlp remote components not configured. Enable --remote-components ejs:github."
            ),
        )

    def _has_js_runtime(self) -> bool:
        return self.resolve_js_runtime() is not None

    def resolve_js_runtime(self) -> "JsRuntime | None":
        if runtime := self._resolve_js_runtime_from_config():
            return runtime
        return self._resolve_js_runtime_from_path()

    def has_remote_components(self) -> bool:
        return self._has_remote_components_config()

    def _resolve_js_runtime_from_path(self) -> "JsRuntime | None":
        for runtime in ("deno", "node", "bun"):
            if path := shutil.which(runtime):
                return JsRuntime(name=runtime, path=Path(path))
        return None

    def _resolve_js_runtime_from_config(self) -> "JsRuntime | None":
        config_path = Path.home() / ".config" / "yt-dlp" / "config"
        if not config_path.exists():
            return None
        try:
            for entry in self._iter_js_runtimes_from_config(config_path):
                if runtime := self._resolve_js_runtime_entry(entry):
                    return runtime
        except OSError:
            return None
        return None

    def _has_remote_components_config(self) -> bool:
        config_path = Path.home() / ".config" / "yt-dlp" / "config"
        if not config_path.exists():
            return False
        try:
            for line in config_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("--remote-components") and "ejs:github" in stripped:
                    return True
        except OSError:
            return False
        return False

    def _iter_js_runtimes_from_config(self, config_path: Path) -> list[str]:
        entries: list[str] = []
        for line in config_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("--js-runtimes"):
                _, _, value = stripped.partition(" ")
                if value:
                    entries.extend([entry.strip() for entry in value.split(",") if entry.strip()])
        return entries

    def _resolve_js_runtime_entry(self, entry: str) -> "JsRuntime | None":
        if ":" in entry:
            name, path = entry.split(":", maxsplit=1)
            path_obj = Path(path)
            if path_obj.exists():
                return JsRuntime(name=name, path=path_obj)
            return None
        if path := shutil.which(entry):
            return JsRuntime(name=entry, path=Path(path))
        return None

    def _has_impersonation_runtime(self) -> bool:
        return self._python_has_curl_cffi() or self._pipx_has_curl_cffi()

    def _python_has_curl_cffi(self) -> bool:
        return importlib.util.find_spec("curl_cffi") is not None

    def _pipx_has_curl_cffi(self) -> bool:
        try:
            result = subprocess.run(
                ["pipx", "runpip", "tnh-scholar", "show", "curl-cffi"],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False


@dataclass(frozen=True)
class JsRuntime:
    name: str
    path: Path
