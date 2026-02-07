import io
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests
import typer
from dotenv import load_dotenv

from tnh_scholar import TNH_CONFIG_DIR, TNH_DEFAULT_PROMPT_DIR, TNH_LOG_DIR
from tnh_scholar.cli_tools.tnh_setup.ui import SetupSummaryItem, SetupUI
from tnh_scholar.utils.validate import check_openai_env
from tnh_scholar.video_processing.yt_environment import YTDLPEnvironmentInspector

app = typer.Typer(add_completion=False, no_args_is_help=False)


@dataclass(frozen=True)
class SetupConfig:
    prompts_url: str
    config_dir: Path
    log_dir: Path
    prompt_dir: Path


@dataclass(frozen=True)
class PromptDecision:
    skip_env: bool
    skip_prompts: bool
    skip_ytdlp_runtime: bool
    verify_only: bool
    assume_yes: bool
    no_input: bool


def _build_config() -> SetupConfig:
    return SetupConfig(
        prompts_url="https://github.com/aaronksolomon/patterns/archive/main.zip",
        config_dir=TNH_CONFIG_DIR,
        log_dir=TNH_LOG_DIR,
        prompt_dir=TNH_DEFAULT_PROMPT_DIR,
    )


def _openai_env_help_msg() -> str:
    return (
        ">>>>>>>>>> OpenAI API key not found in environment. <<<<<<<<<\n\n"
        "For AI processing with TNH-scholar:\n\n"
        "1. Get an API key from https://platform.openai.com/api-keys\n"
        "2. Set the OPENAI_API_KEY environment variable:\n\n"
        "   export OPENAI_API_KEY='your-api-key-here'  # Linux/Mac\n"
        "   set OPENAI_API_KEY=your-api-key-here       # Windows\n\n"
        "For OpenAI API access help: https://platform.openai.com/\n\n"
        ">>>>>>>>>>>>>>>>>>>>>>>>>>> -- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n"
    )


def _create_config_dirs(config: SetupConfig) -> None:
    config.config_dir.mkdir(parents=True, exist_ok=True)
    config.log_dir.mkdir(exist_ok=True)
    config.prompt_dir.mkdir(exist_ok=True)


def _fetch_prompts_zip(url: str) -> bytes:
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def _extract_prompts_zip(zip_bytes: bytes, prompt_dir: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_ref:
        root_dir = zip_ref.filelist[0].filename.split("/")[0]
        for zip_info in zip_ref.filelist:
            if zip_info.filename.endswith(".md"):
                rel_path = Path(zip_info.filename).relative_to(root_dir)
                target_path = prompt_dir / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zip_ref.open(zip_info) as source, open(target_path, "wb") as target:
                    target.write(source.read())


def _download_prompts(config: SetupConfig) -> bool:
    try:
        zip_bytes = _fetch_prompts_zip(config.prompts_url)
        _extract_prompts_zip(zip_bytes, config.prompt_dir)
        return True
    except Exception as exc:  # noqa: BLE001 - broad catch to keep setup resilient
        typer.echo(f"Prompt download failed: {exc}", err=True)
        return False


def _confirm_action(prompt: str, decision: PromptDecision) -> bool:
    if decision.verify_only:
        return False
    if decision.assume_yes:
        return True
    if decision.no_input:
        typer.echo("Non-interactive mode requires --yes or skip flags.", err=True)
        raise typer.Exit(code=1)
    return typer.confirm(prompt)


def _run_ytdlp_runtime_setup(decision: PromptDecision) -> int:
    script_path = Path(__file__).resolve().parents[4] / "scripts" / "setup_ytdlp_runtime.py"
    if not script_path.exists():
        typer.echo(f"  [WARN] runtime setup script not found at {script_path}", err=True)
        return 1
    command = [sys.executable, str(script_path), "--yes"]
    if decision.no_input and not decision.assume_yes:
        command = [sys.executable, str(script_path), "--no-input"]
    result = subprocess.run(command, check=False)
    return result.returncode


def _filter_missing_items(inspector: YTDLPEnvironmentInspector) -> list[str]:
    report = inspector.inspect_report()
    if not report.has_items():
        return []
    return [f"{item.code}: {item.message}" for item in report.items]


def _runtime_is_ready() -> bool:
    inspector = YTDLPEnvironmentInspector()
    return not inspector.inspect_report().has_items()


def _verify_ytdlp_runtime(ui: SetupUI) -> tuple[bool, list[str]]:
    inspector = YTDLPEnvironmentInspector()
    missing_lines = _filter_missing_items(inspector)
    if not missing_lines:
        ui.status("Runtime verification", "verified", "ok")
        return True, []
    ui.status("Runtime verification", "incomplete", "warn")
    for line in missing_lines:
        ui.status("Detail", line, "warn")
    return False, missing_lines


def _check_openai_env(ui: SetupUI) -> bool:
    load_dotenv()
    ok = check_openai_env(output=False)
    if ok:
        ui.status("API key", "verified", "ok")
        return True
    ui.status("API key", "missing", "warn")
    typer.echo(_openai_env_help_msg())
    return False


def _summary_item(component: str, status: str, style: str) -> SetupSummaryItem:
    return SetupSummaryItem(component, status, style)


def _prompt_dir_status(ui: SetupUI, config: SetupConfig) -> tuple[bool, bool]:
    prompt_dir_exists = config.prompt_dir.exists()
    prompt_files = False
    if prompt_dir_exists:
        prompt_files = any(config.prompt_dir.rglob("*.md"))
    prompt_state = "found" if prompt_dir_exists else "missing"
    ui.status("Prompt directory", f"{prompt_state} ({config.prompt_dir})", "info")
    return prompt_dir_exists, prompt_files


def _prompt_skip_item(ui: SetupUI, reason: str) -> SetupSummaryItem:
    ui.status("Prompt download", f"skipped ({reason})", "skip")
    return _summary_item("Prompts", "skipped", "skip")


def _prompt_download(ui: SetupUI, config: SetupConfig) -> SetupSummaryItem:
    ui.status("Prompt source", config.prompts_url, "info")
    success = ui.spinner("Downloading prompts...", lambda: _download_prompts(config))
    if success:
        ui.status("Prompt download", "complete", "ok")
        return _summary_item("Prompts", "installed", "ok")
    ui.status("Prompt download", "failed", "error")
    return _summary_item("Prompts", "failed", "error")


def _handle_prompt_download(
    ui: SetupUI,
    config: SetupConfig,
    decision: PromptDecision,
) -> SetupSummaryItem:
    _, prompt_files = _prompt_dir_status(ui, config)
    if decision.skip_prompts:
        return _prompt_skip_item(ui, "--skip-prompts")
    if decision.verify_only:
        return _prompt_skip_item(ui, "--verify-only")
    if prompt_files:
        ui.status("Prompt files", "detected (download will overwrite)", "warn")
    if not _confirm_action("\nDownload prompt files from GitHub?", decision):
        return _prompt_skip_item(ui, "user declined")
    return _prompt_download(ui, config)


def _runtime_summary(ui: SetupUI, ok: bool, note: str | None) -> SetupSummaryItem:
    status = "verified" if ok else "incomplete"
    if note:
        status = f"{status} ({note})"
    style = "ok" if ok else "warn"
    return _summary_item("yt-dlp runtime", status, style)


def _runtime_verify(ui: SetupUI, note: str | None) -> SetupSummaryItem:
    ok, _ = _verify_ytdlp_runtime(ui)
    return _runtime_summary(ui, ok, note)


def _handle_runtime_setup(ui: SetupUI, decision: PromptDecision) -> SetupSummaryItem:
    ui.status("Runtime check", "starting", "info")
    if decision.skip_ytdlp_runtime:
        return _runtime_verify(ui, "skip setup")
    if decision.verify_only:
        return _runtime_verify(ui, "verify-only")
    if _runtime_is_ready():
        ui.status("Runtime setup", "already verified; skipping prompt", "ok")
        return _runtime_verify(ui, "already verified")
    if _confirm_action(
        "\nSet up yt-dlp runtime dependencies (JS runtime + curl_cffi)?",
        decision,
    ):
        ui.status("Runtime setup", "running", "info")
        runtime_code = _run_ytdlp_runtime_setup(decision)
        if runtime_code != 0:
            ui.status("Runtime setup", "errors reported", "warn")
    return _runtime_verify(ui, None)


def _build_decision(
    skip_env: bool,
    skip_prompts: bool,
    skip_ytdlp_runtime: bool,
    verify_only: bool,
    assume_yes: bool,
    no_input: bool,
) -> PromptDecision:
    return PromptDecision(
        skip_env=skip_env,
        skip_prompts=skip_prompts,
        skip_ytdlp_runtime=skip_ytdlp_runtime,
        verify_only=verify_only,
        assume_yes=assume_yes,
        no_input=no_input,
    )


def _api_key_section(ui: SetupUI, decision: PromptDecision) -> SetupSummaryItem:
    ui.section(1, "Setup API Key")
    if decision.skip_env:
        ui.status("API key", "skipped (--skip-env)", "skip")
        return _summary_item("API key", "skipped", "skip")
    ok = _check_openai_env(ui)
    status = "verified" if ok else "missing"
    style = "ok" if ok else "warn"
    return _summary_item("API key", status, style)


def _prompt_section(
    ui: SetupUI,
    config: SetupConfig,
    decision: PromptDecision,
) -> SetupSummaryItem:
    ui.section(2, "Setup Prompt Directory")
    if not decision.verify_only:
        _create_config_dirs(config)
        ui.status("Config directory", f"ready at {config.config_dir}", "ok")
    else:
        ui.status("Config directory", f"verify-only (target {config.config_dir})", "info")
    return _handle_prompt_download(ui, config, decision)


def _runtime_section(ui: SetupUI, decision: PromptDecision) -> SetupSummaryItem:
    ui.section(3, "Setup YouTube Download Support")
    return _handle_runtime_setup(ui, decision)


def _run_setup(config: SetupConfig, decision: PromptDecision) -> None:
    ui = SetupUI.create()
    ui.banner()
    summary = [
        _api_key_section(ui, decision),
        _prompt_section(ui, config, decision),
        _runtime_section(ui, decision),
    ]
    ui.summary(summary)


@app.command()
def tnh_setup(
    skip_env: bool = typer.Option(False, help="Skip OpenAI API key check."),
    skip_prompts: bool = typer.Option(False, help="Skip prompt download."),
    skip_ytdlp_runtime: bool = typer.Option(False, help="Skip yt-dlp runtime setup."),
    verify_only: bool = typer.Option(False, help="Only run environment verification."),
    assume_yes: bool = typer.Option(False, "--yes", "-y", help="Assume yes for all prompts."),
    no_input: bool = typer.Option(False, help="Fail if a prompt would be required."),
) -> None:
    """Set up TNH Scholar configuration."""
    config = _build_config()
    decision = _build_decision(
        skip_env=skip_env,
        skip_prompts=skip_prompts,
        skip_ytdlp_runtime=skip_ytdlp_runtime,
        verify_only=verify_only,
        assume_yes=assume_yes,
        no_input=no_input,
    )
    _run_setup(config, decision)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
