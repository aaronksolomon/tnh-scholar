import argparse
import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class RuntimeDetection:
    name: str
    path: Path


@dataclass(frozen=True)
class CurlCffiStatus:
    current_env: bool
    pipx_env: bool

    def any_available(self) -> bool:
        return self.current_env or self.pipx_env


@dataclass(frozen=True)
class SetupResult:
    js_runtime: RuntimeDetection | None
    curl_status: CurlCffiStatus
    config_written: bool
    errors: tuple[str, ...]

    def ok(self) -> bool:
        return not self.errors


@dataclass
class RuntimeSetup:
    runner: Callable[..., subprocess.CompletedProcess[str]]
    which: Callable[[str], str | None]
    input_func: Callable[[str], str]

    def find_js_runtime(self) -> RuntimeDetection | None:
        for runtime in ("deno", "node", "bun"):
            if path := self.which(runtime):
                return RuntimeDetection(name=runtime, path=Path(path))
        return None

    def python_has_curl_cffi(self) -> bool:
        return importlib.util.find_spec("curl_cffi") is not None

    def pipx_has_curl_cffi(self) -> bool:
        try:
            result = self.runner(
                ["pipx", "runpip", "tnh-scholar", "show", "curl-cffi"],
                env=self._pipx_env(),
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except OSError:
            return False

    def _pipx_env(self) -> dict[str, str]:
        log_dir = Path.home() / ".local" / "pipx" / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            return {}
        return {"PIPX_LOG_DIR": str(log_dir)}

    def curl_status(self) -> CurlCffiStatus:
        return CurlCffiStatus(
            current_env=self.python_has_curl_cffi(),
            pipx_env=self.pipx_has_curl_cffi(),
        )

    def brew_available(self) -> bool:
        return self.which("brew") is not None

    def install_js_runtime(self, assume_yes: bool, no_input: bool) -> tuple[RuntimeDetection | None, list[str]]:
        if runtime := self.find_js_runtime():
            print("JS runtime detected.")
            return runtime, []
        if self.brew_available():
            return self._install_js_runtime_with_brew(assume_yes, no_input)
        self._print_runtime_guidance()
        return None, ["JS runtime missing."]

    def _install_js_runtime_with_brew(
        self, assume_yes: bool, no_input: bool
    ) -> tuple[RuntimeDetection | None, list[str]]:
        if self.confirm("No JS runtime found. Install deno via brew? [y/N] ", assume_yes, no_input):
            result = self.runner(["brew", "install", "deno"], check=False)
            if result.returncode != 0:
                return None, ["brew install deno failed"]
        runtime = self.find_js_runtime()
        return (runtime, []) if runtime else (None, ["JS runtime not installed."])

    def _print_runtime_guidance(self) -> None:
        print("No JS runtime found. Install one of: deno, node, bun.")
        print("- macOS (brew): brew install deno")
        print("- node: https://nodejs.org/")
        print("- bun: https://bun.sh/")

    def install_curl_cffi(self, assume_yes: bool, no_input: bool) -> list[str]:
        if self.python_has_curl_cffi():
            print("curl_cffi detected (current env).")
            return []
        if self.pipx_has_curl_cffi():
            print("curl_cffi detected (pipx env).")
            return []
        return self._prompt_install_curl_cffi(assume_yes, no_input)

    def _prompt_install_curl_cffi(self, assume_yes: bool, no_input: bool) -> list[str]:
        install_cmd = self._install_command()
        print("curl_cffi not found.")
        if self.confirm(f"Install with: {install_cmd}? [y/N] ", assume_yes, no_input):
            result = self._run_install_command(install_cmd)
            if result.returncode != 0 and install_cmd.startswith("pipx "):
                fallback = self._fallback_install_command()
                print(f"pipx install failed. Trying fallback: {fallback}")
                result = self._run_install_command(fallback)
                install_cmd = fallback
            if result.returncode != 0:
                return [self._install_failure_message(install_cmd)]
            return []
        return ["curl_cffi not installed."]

    def _install_command(self) -> str:
        root = self.repo_root()
        if self.which("pipx"):
            return "pipx inject tnh-scholar curl_cffi"
        if self.which("poetry") and (root / "pyproject.toml").exists():
            return "poetry run python -m pip install curl_cffi"
        return "python -m pip install curl_cffi"

    def _fallback_install_command(self) -> str:
        root = self.repo_root()
        if self.which("poetry") and (root / "pyproject.toml").exists():
            return "poetry run python -m pip install curl_cffi"
        return "python -m pip install curl_cffi"

    def _run_install_command(self, install_cmd: str) -> subprocess.CompletedProcess[str]:
        if install_cmd.startswith("pipx "):
            try:
                return self.runner(
                    install_cmd.split(" "),
                    env=self._pipx_env(),
                    check=False,
                )
            except FileNotFoundError:
                return self._failed_process()
        try:
            return self.runner(install_cmd.split(" "), check=False)
        except FileNotFoundError:
            return self._failed_process()

    def _install_failure_message(self, install_cmd: str) -> str:
        if install_cmd.startswith("pipx "):
            return "curl_cffi install failed (pipx). Check pipx is installed and PIPX_LOG_DIR permissions."
        if install_cmd.startswith("poetry "):
            return "curl_cffi install failed (poetry). Run 'poetry run python -m pip install curl_cffi'."
        return "curl_cffi install failed"

    def _failed_process(self) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=1)

    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def write_config(self, runtime: RuntimeDetection, curl_status: CurlCffiStatus) -> tuple[bool, str | None]:
        config_dir = Path.home() / ".config" / "yt-dlp"
        config_path = config_dir / "config"
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            lines = self._config_lines(runtime, curl_status)
            config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"Wrote yt-dlp config to {config_path}")
            return True, None
        except OSError as exc:
            message = f"Failed to write yt-dlp config: {exc}"
            print(message)
            return False, message

    def _config_lines(self, runtime: RuntimeDetection, curl_status: CurlCffiStatus) -> tuple[str, ...]:
        header = "# Generated by tnh-setup / setup_ytdlp_runtime.py"
        runtime_line = f"--js-runtimes {runtime.name}:{runtime.path}"
        lines = [header, runtime_line, "--remote-components ejs:github"]
        if curl_status.any_available():
            lines.append("--impersonate chrome")
        return tuple(lines)

    def confirm(self, prompt: str, assume_yes: bool, no_input: bool) -> bool:
        if assume_yes:
            return True
        if no_input:
            raise RuntimeError("Non-interactive mode requires --yes or skip flags.")
        reply = self.input_func(prompt).strip()
        return reply.lower().startswith("y")

    def print_status(self, runtime: RuntimeDetection | None, curl_status: CurlCffiStatus) -> None:
        self._print_runtime_status(runtime)
        self._print_curl_status(curl_status)

    def _print_runtime_status(self, runtime: RuntimeDetection | None) -> None:
        if runtime:
            print(f"JS runtime: {runtime.name}:{runtime.path}")
        else:
            print("JS runtime: missing")

    def _print_curl_status(self, curl_status: CurlCffiStatus) -> None:
        current = "installed" if curl_status.current_env else "missing"
        pipx = "installed" if curl_status.pipx_env else "missing"
        print(f"curl_cffi (current env): {current}")
        print(f"curl_cffi (pipx env): {pipx}")


def _build_setup() -> RuntimeSetup:
    return RuntimeSetup(
        runner=subprocess.run,
        which=shutil.which,
        input_func=input,
    )


def _run_steps(setup: RuntimeSetup, assume_yes: bool, no_input: bool) -> tuple[RuntimeDetection | None, list[str]]:
    runtime, runtime_errors = setup.install_js_runtime(assume_yes, no_input)
    curl_errors = setup.install_curl_cffi(assume_yes, no_input)
    errors = runtime_errors + curl_errors
    return runtime, errors


def run_setup(assume_yes: bool, no_input: bool) -> SetupResult:
    setup = _build_setup()
    print("yt-dlp runtime setup")
    runtime, errors = _run_steps(setup, assume_yes, no_input)
    curl_status = setup.curl_status()
    config_written, config_errors = _write_config_if_possible(setup, runtime, curl_status)
    errors.extend(config_errors)
    setup.print_status(runtime, curl_status)
    _print_done(errors)
    return SetupResult(
        js_runtime=runtime,
        curl_status=curl_status,
        config_written=config_written,
        errors=tuple(errors),
    )


def _write_config_if_possible(
    setup: RuntimeSetup,
    runtime: RuntimeDetection | None,
    curl_status: CurlCffiStatus,
) -> tuple[bool, list[str]]:
    if runtime is None:
        print("Skipping yt-dlp config: no JS runtime found.")
        return False, ["yt-dlp config not written (missing JS runtime)."]
    wrote, message = setup.write_config(runtime, curl_status)
    return wrote, [message] if message else []


def _print_done(errors: list[str]) -> None:
    if errors:
        print("Done with warnings.")
    else:
        print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up yt-dlp runtime dependencies.")
    parser.add_argument("--yes", action="store_true", help="Assume yes for prompts.")
    parser.add_argument("--no-input", action="store_true", help="Fail if prompts are required.")
    args = parser.parse_args()
    try:
        result = run_setup(assume_yes=args.yes, no_input=args.no_input)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
    raise SystemExit(0 if result.ok() else 1)


if __name__ == "__main__":
    main()
