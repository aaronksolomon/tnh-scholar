# TNH‑Scholar Utilities Catalog

This catalog lists core utility modules used across the TNH‑Scholar codebase. It provides a quick reference for shared abstractions, their purpose, API highlights, and stability. All modules are currently in **Prototype** phase, with most stable in active use.

| Status      | Meaning                                         |
|-------------|-------------------------------------------------|
| Stable      | Used widely; interface considered reliable      |
| Evolving    | Actively refined; API may change                |
| Experimental| Early or niche use; subject to major revision   |

## timing_utils.py — Stable

**Module:** `tnh_scholar.utils.timing_utils`

**Purpose:** Small, explicit time type for millisecond-based values. Replaces ad-hoc float timestamps and makes conversions and arithmetic explicit and type-safe.

**Key APIs:**

- `class TimeMs(int)` — lightweight typed integer representing milliseconds. Supports construction from int/float/TimeMs, arithmetic (+, -, radd, rsub), and pydantic core schema integration.
- `TimeMs.from_seconds(seconds: float) -> TimeMs` — construct from seconds.
- `TimeMs.to_ms() -> int` — return milliseconds as int.
- `TimeMs.to_seconds() -> float` — return seconds as float.
- `convert_sec_to_ms(val: float) -> int` — helper to convert seconds to ms (rounded).
- `convert_ms_to_sec(ms: int) -> float` — helper to convert ms to seconds.

**Used by:** Any module that needs deterministic millisecond arithmetic or pydantic models (e.g., provenance, latency reporting).

**Notes:** Designed to be small and explicit; does not attempt to provide clocks or wall-time semantics — that belongs in an Observer/tracer implementation.

## json_utils.py — Stable

**Module:** `tnh_scholar.utils.json_utils`

**Purpose:** Robust JSON helpers for files and pydantic models: read/write JSON, load JSONL, and format files consistently.

**Key APIs:**

- `write_data_to_json_file(file: Path, data: dict | list, indent=4, ensure_ascii=False) -> None` — serialize data to JSON and write to disk, creating parent folders.
- `save_model_to_json(file: Path, model: BaseModel, indent=4, ensure_ascii=False) -> None` — dump a Pydantic model (uses `model_dump()`), writing via `write_data_to_json_file`.
- `load_jsonl_to_dict(file_path: Path) -> list[dict]` — read a JSONL file into a list of dicts.
- `load_json_into_model(file: Path, model: type[BaseModel]) -> BaseModel` — load JSON and validate/construct the given Pydantic model type (raises ValueError on failure).
- `format_json(file: Path) -> None` — read and re-write JSON file with indentation and ensure_ascii=False.

**Used by:** Config I/O, model persistence, dataset pre-processing, and simple scripting tasks.

**Notes:** Functions raise informative exceptions (ValueError / IOError) on failure to make error handling explicit to callers.

## lang.py — Stable

**Module:** `tnh_scholar.utils.lang`

**Purpose:** Language detection helpers using `langdetect` for short samples and `pycountry` for mapping codes to English names.

**Key APIs:**

- `get_language_code_from_text(text: str) -> str` — returns ISO-639-1 code (e.g., 'en') or 'un' when detection fails; raises ValueError if input is empty.
- `get_language_name_from_text(text: str) -> str` — returns English language name for detected code (uses `pycountry`).
- `get_language_from_code(code: str) -> str` — maps ISO code to human name or returns 'Unknown' with a warning.
- `_get_sample_text(text: str, words_per_sample: int = 30) -> str` — internal helper that extracts 3 samples (start, 1/3, 2/3) to improve detection for long text.

**Used by:** Metadata extraction, normalization, and any pipeline that needs a quick language hint.

**Notes:** Defensive for long/short texts; returns 'un' when detection fails to avoid exceptions in pipelines.

## file_utils.py — Stable

**Module:** `tnh_scholar.utils.file_utils`

**Purpose:** Common filesystem helpers used by CLI and batch jobs: ensure directories, write/read strings, copy files matching patterns, and filename sanitization.

**Key APIs:**

- `DEFAULT_MAX_FILENAME_LENGTH: int` — default max length used by sanitizers.
- `FileExistsWarning` — custom warning class.
- `ensure_directory_exists(dir_path: Path) -> bool` — mkdir -p semantics; returns True on success.
- `ensure_directory_writable(dir_path: Path) -> None` — verifies/creates dir and tests writability using a NamedTemporaryFile (raises on failure).
- `iterate_subdir(directory: Path, recursive: bool = False) -> Generator[Path, None, None]` — yield subdirectory Paths (one level or recursive).
- `path_source_str(path: Path) -> str` — return resolved string path.
- `copy_files_with_regex(source_dir: Path, destination_dir: Path, regex_patterns: list[str], preserve_structure: bool = True) -> None` — copy files one level down that match patterns; creates destination directories as needed.
- `read_str_from_file(file_path: Path) -> str` — read full text content.
- `write_str_to_file(file_path: PathLike, text: str, overwrite: bool = False) -> None` — write text with optional overwrite guard.
- `sanitize_filename(filename: str, max_length: int = DEFAULT_MAX_FILENAME_LENGTH) -> str` — normalize/slugify and truncate to safe ascii filename.
- `to_slug(string: str) -> str` — produce a URL‑friendly slug (lowercase, hyphens).
- `path_as_str(path: Path) -> str` — alias for resolved path as string.

**Used by:** Any code that reads/writes files, prepares artifacts for storage, or needs consistent filename handling.

**Notes:** The module intentionally surfaces IO exceptions for callers to handle; it prefers explicit failures in prototype code.

## user_io_utils.py — Stable

**Module:** `tnh_scholar.utils.user_io_utils`

**Purpose:** Small cross-platform console utilities for interactive scripts (single-character input, confirmation prompts), with fallbacks for Jupyter/IPython.

**Key APIs:**

- `get_single_char(prompt: Optional[str] = None) -> str` — read a single character without requiring Enter in terminal environments; falls back to `input()` in notebooks.
- `get_user_confirmation(prompt: str, default: bool = True) -> bool` — prompt for a y/n confirmation using `get_single_char`; returns default on Enter.

**Used by:** CLI scripts, interactive tooling, and any dev tooling that wants compact confirmations.

**Notes:** The implementation handles Windows (msvcrt) and Unix (termios/tty) cases and deliberately falls back in interactive notebook environments.

## validate.py — Stable

**Module:** `tnh_scholar.utils.validate`

**Purpose:** Lightweight environment checks and user-facing error messages for required environment variables and features.

**Key APIs:**

- `get_env_message(missing_vars: List[str], feature: str = "this feature") -> str` — human-friendly message explaining how to set missing env vars.
- `check_env(required_vars: Set[str], feature: str = "this feature", output: bool = True) -> bool` — returns True if all required vars are present; logs/prints helpful message if not.
- `check_openai_env(output: bool = True) -> bool` — convenience wrapper checking `OPENAI_API_KEY`.
- `check_ocr_env(output: bool = True) -> bool` — convenience wrapper checking `GOOGLE_APPLICATION_CREDENTIALS`.

**Used by:** Startup checks, test harnesses, and preflight validation in scripts.

## logging_config.py — Stable

**Module:** `tnh_scholar.logging_config`

**Purpose:** Centralized, production-grade logging configuration for the entire TNH-Scholar system. Provides color/plain text logs in development, JSON logs in production, queue-based asynchronous logging, file rotation, noise suppression, and Python warnings capture. Designed for library compatibility and app-layer configurability.

**Key APIs:**

- `setup_logging(...)` — main initializer; reads environment variables to configure log level, handlers, formatters, and rotation. Should be called once by the *application layer* (CLI, Streamlit, API service).
- `get_logger(name: str)` — preferred helper to retrieve a logger for a given module or component.
- `get_child_logger(name: str, console=False, separate_file=False)` — legacy helper for modules needing ad-hoc console or file handlers; maintained for backward compatibility.
- `setup_logging_legacy(...)` — deprecated alias to `setup_logging()` with a `DeprecationWarning`.
- `priority_info(message, *args, **kwargs)` — legacy helper method on logger instances; emits at custom level 25 with a deprecation warning; prefer `logger.info(..., extra={"priority": "high"})`.

**Environment Variables:**

- `APP_ENV`: `dev` | `prod` | `test` (default: `dev`)
- `LOG_JSON`: `true|false` (enable JSON output; default true in prod)
- `LOG_STDOUT`: `true|false` (emit to stdout)
- `LOG_FILE_ENABLE`: `true|false`
- `LOG_FILE_PATH`: path to log file (default `./logs/main.log`)
- `LOG_ROTATE_BYTES`, `LOG_ROTATE_WHEN`, `LOG_BACKUPS`: control file rotation
- `LOG_USE_QUEUE`: `true|false` (async logging)
- `LOG_STREAM`: `stdout|stderr` (default `stderr`; dev defaults to `stdout`)
- `LOG_COLOR`: `true|false|auto`
- `LOG_CAPTURE_WARNINGS`: `true|false` (redirect Python warnings)
- `LOG_SUPPRESS`: comma-separated list of noisy modules to set to WARNING
- `LOG_LEVEL`: base log level (default `INFO`)

**Usage:**

- Application entrypoint:

  ```python
  from tnh_scholar.logging_config import setup_logging, get_logger
  setup_logging()  # read from environment
  log = get_logger(__name__)
  log.info("app started", extra={"service": "gen-ai"})
  ```

- Library/service:

  ```python
  from tnh_scholar.logging_config import get_logger
  log = get_logger(__name__)
  log.debug("internal operation")
  ```

**Backward Compatibility:**

- Supports existing modules using `get_child_logger(__name__)` without change.
- Legacy custom level `PRIORITY_INFO` retained for compatibility but deprecated.

**Notes:**

- Does not configure the *root* logger; uses the project base logger (`tnh`) for isolation.
- Default behavior:
  - **dev:** plain or color text, stdout, no queue.
  - **prod:** JSON logs to stderr, queue enabled, suitable for structured log collection.
- Integrates with Python’s `logging.captureWarnings()` when enabled.

## progress_utils.py — Experimental

**Module:** `tnh_scholar.utils.progress_utils`

**Purpose:** Time-based progress displays. Provides both a tqdm-backed expected-time bar (with delayed start to avoid flicker) and a simple dot/spinner progress for lightweight cases.

**Key APIs:**

- `ExpectedTimeTQDM(expected_time: float, display_interval: float = 0.5, desc: str = "Time-based Progress", delay_start: float = 1.0)` — context manager that shows a tqdm bar after an optional delay.
- `TimeProgress(expected_time: Optional[float] = None, display_interval: float = 1.0, desc: str = "")` — context manager printing a lightweight spinner/dots with elapsed/expected time.

**Notes:** Both are intended for CLI tooling (not GUI). `ExpectedTimeTQDM` spawns a background thread to update the bar and avoids creating the bar if the task completes before `delay_start`.

## tnh_audio_segment.py — Stable

**Module:** `tnh_scholar.utils.tnh_audio_segment`

**Purpose:** Thin, typed wrapper around `pydub.AudioSegment` to give clearer typing, a small API surface, and convenience constructors used by the audio pipeline.

**Key APIs:**

- `class TNHAudioSegment` — wrapper with methods:
  - `from_file(file: str | Path | BytesIO, format: str | None = None, **kwargs) -> TNHAudioSegment`
  - `export(out_f: str | BinaryIO, format: str, **kwargs) -> None`
  - `silent(duration: int) -> TNHAudioSegment`
  - `empty() -> TNHAudioSegment`
  - `__getitem__(key: int | slice) -> TNHAudioSegment`
  - `__add__`, `__iadd__`, `__len__`, and `raw` property exposing underlying `_AudioSegment`.

**Used by:** Audio ingestion, concatenation, slicing, and export in diarization/transcription flows.

## webhook_server.py — Evolving

**Module:** `tnh_scholar.utils.webhook_server`

**Purpose:** Small development helper to run a local Flask webhook endpoint and (optionally) create a public tunnel via `pylt` (localtunnel client). Useful for testing provider callbacks and webhooks during development.

**Key APIs:**

- `class WebhookServer` — convenience wrapper providing:
  - `start_server(host: str = "127.0.0.1", port: int = 0) -> str` — starts a local Flask server on an available port; returns server URL.
  - `wait_for_webhook(timeout: float = 30.0) -> dict | None` — block until a webhook payload arrives or timeout; returns parsed payload.
  - `create_tunnel(subdomain: Optional[str] = None) -> str` — spawn `pylt` subprocess to create a tunnel and return the public URL (relies on `pylt` being installed).
  - `close_tunnel()` — terminate the tunnel subprocess safely.
  - `shutdown_server()` and `cleanup()` — helper methods to stop the server and any background processes.

**Notes:** This module is primarily for local development. The tunnel creation parses subprocess stdout/stderr and depends on the `pylt` client; use with care in CI or headless environments.

## Observability / obs (doc-only)

The design docs reference a lightweight Observer/ObsSpan protocol used to capture phase timings and attach metadata to spans. The docs include small Protocol examples (ObsSpan as a context manager with `duration_ms` and `Observer.phase(name, **fields) -> ObsSpan`) and a `NoOpObserver` used for tests or when tracing is not needed.
