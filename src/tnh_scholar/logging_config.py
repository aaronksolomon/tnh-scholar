"""TNH-Scholar Logging Utilities
=================================

A production-ready, environment-driven logging system for the TNH-Scholar project.
It provides JSON logs in production, color/plain text in development, optional
non-blocking queue logging, file rotation, noise suppression for chatty deps,
and optional routing of Python warnings into the logging pipeline.

This module is designed for *application layer* configuration and *library layer*
usage:

- **Applications** (CLI, Streamlit, FastAPI, notebooks) call :func:`setup_logging`.
- **Libraries / services** (e.g., gen_ai_service, IssueHandler) only *acquire* a
  logger via :func:`get_logger` (or legacy :func:`get_child_logger`) and never
  configure global logging.

-------------------------------------------------------------------------------
Quick start
-------------------------------------------------------------------------------
Application entry point (recommended):

    >>> from tnh_scholar.logging_config import setup_logging, get_logger
    >>> setup_logging()  # reads env; see variables below
    >>> log = get_logger(__name__)
    >>> log.info("app started", extra={"service": "gen-ai"})

Jupyter / dev (force color in non-TTY):

    >>> import os
    >>> os.environ["APP_ENV"] = "dev"
    >>> os.environ["LOG_JSON"] = "false"
    >>> os.environ["LOG_COLOR"] = "true"]  # Jupyter isn't a TTY; force color
    >>> from tnh_scholar.logging_config import setup_logging, get_logger
    >>> setup_logging()
    >>> get_logger(__name__).info("hello, color")

Library / service modules (do NOT configure logging):

    >>> from tnh_scholar.logging_config import get_logger
    >>> log = get_logger(__name__)
    >>> log.info("library message")

-------------------------------------------------------------------------------
Behavior by environment
-------------------------------------------------------------------------------
- **dev** (default):
    * Plain or color text to **stdout** by default.
    * Queue logging **disabled** by default (synchronous).
    * Color auto-detects TTY *and* Jupyter/IPython (can be forced).
- **prod**:
    * JSON logs to **stderr** by default (suitable for log shippers).
    * Queue logging **enabled** by default (can be disabled).

-------------------------------------------------------------------------------
Environment variables
-------------------------------------------------------------------------------
Most behavior is controlled by environment variables (read when `setup_logging()`
instantiates :class:`LogSettings`). Truthy values accept `true/1/yes/on`
(case-insensitive).

- ``APP_ENV``: ``dev`` | ``prod`` | ``test`` (default: ``dev``)
- ``LOG_LEVEL``: Logging level for the base project logger (default: ``INFO``)
- ``LOG_STDOUT``: Emit logs to stdout (default: ``true``)
- ``LOG_FILE_ENABLE``: Emit logs to a file (default: ``false``)
- ``LOG_FILE_PATH``: File path for logs (default: ``./logs/main.log``)
- ``LOG_ROTATE_BYTES``: Rotate at N bytes (e.g., 10485760) (default: unset)
- ``LOG_ROTATE_WHEN``: Timed rotation (e.g., ``midnight``) (default: unset)
- ``LOG_BACKUPS``: Number of rotated file backups (default: ``5``)
- ``LOG_JSON``: Use JSON formatter (recommended in prod) (default: ``true``)
- ``LOG_COLOR``: ``true`` | ``false`` | ``auto`` (default: ``auto``)
- ``LOG_STREAM``: ``stdout`` | ``stderr`` (default: ``stderr``; **dev** defaults to ``stdout``)
- ``LOG_USE_QUEUE``: Use QueueHandler/QueueListener (default: ``true``; **dev** defaults to ``false``)
- ``LOG_CAPTURE_WARNINGS``: Route Python warnings via logging (default: ``false``)
- ``LOG_SUPPRESS``: Comma-separated list of noisy module names to set to WARNING
                    (default includes ``urllib3``, ``httpx``, ``openai``, ``uvicorn.*``, etc.)

-------------------------------------------------------------------------------
Backward compatibility
-------------------------------------------------------------------------------
- **`get_child_logger(name, console=False, separate_file=False)`** remains available
  and can attach ad-hoc console/file handlers without reconfiguring the project
  base logger. When custom handlers are attached, the child’s propagation is turned
  off to avoid duplicate messages.
- **`setup_logging_legacy(...)`** forwards to :func:`setup_logging` and emits
  a DeprecationWarning to help locate legacy call sites.
- **Custom level `PRIORITY_INFO` (25)** and :meth:`logger.priority_info` still exist
  but are **deprecated**. Prefer:

    >>> log.info("message", extra={"priority": "high"})

  This keeps level semantics standard and plays better with structured logging.

-------------------------------------------------------------------------------
Queue logging notes
-------------------------------------------------------------------------------
- When ``LOG_USE_QUEUE=true``, the base logger uses a :class:`QueueHandler`.
  A :class:`QueueListener` is started with sinks mirroring your configured
  stdout/file handlers. This decouples log emission from I/O to minimize latency.
- In notebooks or during debugging, you may prefer synchronous logs:

    >>> os.environ["LOG_USE_QUEUE"] = "false"

-------------------------------------------------------------------------------
Python warnings routing
-------------------------------------------------------------------------------
- When ``LOG_CAPTURE_WARNINGS=true``, Python warnings are captured and logged
  through ``py.warnings``. This module attaches the base logger’s handlers to
  that logger and disables propagation to avoid duplicate output.

-------------------------------------------------------------------------------
Mixing print() and logging
-------------------------------------------------------------------------------
- `print()` writes to **stdout**; the logger can write to **stdout** or **stderr**
  depending on ``LOG_STREAM`` and environment. Ordering is not guaranteed,
  especially with queue logging enabled. Prefer logging for consistent output.

-------------------------------------------------------------------------------
Minimal examples
-------------------------------------------------------------------------------
CLI / entrypoint:

    >>> import os
    >>> os.environ.setdefault("APP_ENV", "prod")
    >>> os.environ.setdefault("LOG_JSON", "true")
    >>> from tnh_scholar.logging_config import setup_logging, get_logger
    >>> setup_logging()
    >>> get_logger(__name__).info("ready")

File logging with rotation:

    >>> import os
    >>> os.environ.update({
    ...     "LOG_FILE_ENABLE": "true",
    ...     "LOG_FILE_PATH": "./logs/app.log",
    ...     "LOG_ROTATE_BYTES": "10485760",  # 10MB
    ...     "LOG_BACKUPS": "7",
    ... })
    >>> setup_logging()
    >>> get_logger("smoke").info("to file")

Jupyter with color:

    >>> import os
    >>> os.environ.update({"APP_ENV": "dev", "LOG_JSON": "false", "LOG_COLOR": "true"})
    >>> setup_logging()
    >>> get_logger(__name__).info("color in notebook")

-------------------------------------------------------------------------------
Notes
-------------------------------------------------------------------------------
- JSON formatting requires ``python-json-logger``; without it, we fall back to
  plain/color format automatically.
- This module never configures the *root* logger; it configures the project
  base logger (``tnh``) so your app can coexist with other libraries cleanly.
"""


import contextlib
import logging
import logging.config
import os
import queue
import sys
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

import colorlog

# TODO Run sourcery on this file. Some lingering minor issues to address.

try:
    # import the module rather than the class to avoid reassigning an imported type name
    import pythonjsonlogger.json as _pythonjsonlogger_json  # type: ignore
    from pythonjsonlogger import jsonlogger  # pip install python-json-logger
    JsonFormatter = getattr(_pythonjsonlogger_json, "JsonFormatter", None)
except Exception:
    jsonlogger = None
    JsonFormatter = None

BASE_LOG_NAME = "tnh"  # tnh-scholar project
BASE_LOG_DIR = Path("./logs")
DEFAULT_LOG_FILEPATH = Path("main.log")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 mb

# Define custom log level: PRIORITY_INFO
PRIORITY_INFO_LEVEL = 25
logging.addLevelName(PRIORITY_INFO_LEVEL, "PRIORITY_INFO")


def priority_info(self, message, *args, **kwargs):
    """
    Deprecated: use `logger.info(msg, extra={"priority": "high"})` instead.

    This custom level (25) was introduced for highlighting important informational
    events, but it complicates interoperability with external log shippers and
    structured log processing. The recommended migration path is to log at the
    standard INFO level with an added `extra` field indicating priority.

    Example:
        >>> logger.info("Important event", extra={"priority": "high"})
    """
    warnings.warn(
        "logger.priority_info() is deprecated; use logger.info(..., extra={'priority': 'high'}) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if self.isEnabledFor(PRIORITY_INFO_LEVEL):
        # Log normally at PRIORITY_INFO_LEVEL for backward compatibility
        self._log(PRIORITY_INFO_LEVEL, message, args, **kwargs)
    else:
        # Fallback to standard INFO level if not explicitly handled
        self.info(message, *args, **kwargs)


# Add PRIORITY_INFO to the Logger class
setattr(logging.Logger, "priority_info", priority_info)

# Define log colors
LOG_COLORS = {
    "DEBUG": "bold_green",
    "INFO": "cyan",
    "PRIORITY_INFO": "bold_cyan",
    "WARNING": "bold_yellow",
    "ERROR": "bold_red",
    "CRITICAL": "bold_red",
}

# --- Centralized format strings (single source of truth) ---
LOG_FMT_PLAIN = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_FMT_COLOR = "%(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | %(name)s | %(message)s"
LOG_FMT_JSON = (
    "%(asctime)s %(levelname)s %(name)s %(message)s "
    "%(process)d %(thread)d %(module)s %(filename)s %(lineno)d"
)
# Legacy defaults kept for backward-compat call sites using get_child_logger()
DEFAULT_CONSOLE_FORMAT_STRING = LOG_FMT_COLOR
DEFAULT_FILE_FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- Env helpers (evaluated at instantiation time) ---
def _env_str(key: str, default: str) -> str:
    return os.getenv(key, default)

def _env_bool(key: str, default: str) -> bool:
    val = os.getenv(key, default)
    return val.strip().lower() in ("true", "1", "yes", "on")

def _env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    try:
        return int(val) if val is not None and val.strip() != "" else default
    except Exception:
        return default

def _is_tty(stream) -> bool:
    try:
        return hasattr(stream, "isatty") and stream.isatty()
    except Exception:
        return False

class UtcFormatter(logging.Formatter):
    """UTC ISO-8601 timestamps for plain text logging."""
    # logging.Formatter.converter must accept (float | None) and return struct_time;
    # time.gmtime satisfies that contract and returns a UTC struct_time.
    converter = time.gmtime

    def formatTime(self, record, datefmt=None):
        if datefmt:
            return super().formatTime(record, datefmt)
        return datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()


@dataclass
class LogSettings:
    """Environment-driven logging settings with sensible defaults."""
    # Mode
    environment: str = field(default_factory=lambda: _env_str("APP_ENV", "dev"))  # dev|prod|test
    base_name: str = field(default_factory=lambda: _env_str("LOG_BASE", BASE_LOG_NAME))

    # Level
    level: str = field(default_factory=lambda: _env_str("LOG_LEVEL", "INFO"))

    # Outputs
    to_stdout: bool = field(default_factory=lambda: _env_bool("LOG_STDOUT", "true"))
    to_file: bool = field(default_factory=lambda: _env_bool("LOG_FILE_ENABLE", "false"))
    file_path: Path = field(
        default_factory=lambda: Path(
            _env_str("LOG_FILE_PATH", str(BASE_LOG_DIR / DEFAULT_LOG_FILEPATH))
            )
        )

    # File rotation
    rotate_when: Optional[str] = field(default_factory=lambda: _env_str("LOG_ROTATE_WHEN", "") or None)  
        # e.g. 'midnight'
    rotate_bytes: Optional[int] = field(default_factory=lambda: (_env_int("LOG_ROTATE_BYTES", 0) or None))  
        # e.g. 10485760
    backups: int = field(default_factory=lambda: _env_int("LOG_BACKUPS", 5))

    # Format
    json_format: bool = field(default_factory=lambda: _env_bool("LOG_JSON", "true"))  # prod default
    colorize: str = field(default_factory=lambda: _env_str("LOG_COLOR", "auto"))  # true|false|auto

    # Python warnings routing
    capture_warnings: bool = field(default_factory=lambda: _env_bool("LOG_CAPTURE_WARNINGS", "false"))

    # Stream selection (stdout|stderr)
    log_stream: str = field(default_factory=lambda: _env_str("LOG_STREAM", "stderr"))

    # Performance
    use_queue: bool = field(default_factory=lambda: _env_bool("LOG_USE_QUEUE", "true"))

    # Noise suppression (comma-separated)
    suppress_modules: str = field(default_factory=lambda: _env_str(
        "LOG_SUPPRESS",
        "urllib3,httpx,openai,botocore,boto3,asyncio,uvicorn,uvicorn.error,uvicorn.access",
    ))

    def is_dev(self) -> bool:
        return self.environment.lower() == "dev"

    def should_color(self) -> bool:
        if self.colorize == "true":
            return True
        if self.colorize == "false":
            return False
        # auto: TTY or Jupyter/IPython
        if _is_tty(self.selected_stream()):
            return True
        try:
            from IPython.core.getipython import get_ipython
            return get_ipython() is not None  # in a notebook/console
        except Exception:
            return False

    def selected_stream(self):
        """Return the Python stream object to emit logs to (stdout or stderr)."""
        return sys.stdout if self.log_stream.lower() == "stdout" else sys.stderr

    def __post_init__(self):
        # Default to stdout and no-queue in dev, unless explicitly overridden by env
        if self.is_dev():
            if "LOG_STREAM" not in os.environ:
                self.log_stream = "stdout"
            if "LOG_USE_QUEUE" not in os.environ:
                self.use_queue = False


_queue_listener: Optional[QueueListener] = None

class LoggingConfigurator:
    _queue: Optional[queue.Queue] = None

    # ----- Private helpers (handlers) -----
    def _stdout_handler_config(self, fmt_key: str) -> dict:
        stream_path = "ext://sys.stdout" if self.settings.log_stream.lower() == "stdout" else "ext://sys.stderr"
        return {
            "class": "logging.StreamHandler",
            "stream": stream_path,
            "formatter": fmt_key,
            "filters": ["omp_filter"],
        }

    def _file_handler_config(self, *, formatter_key: str) -> dict:
        s = self.settings
        s.file_path.parent.mkdir(parents=True, exist_ok=True)
        if s.rotate_bytes:
            return {
                "class": "logging.handlers.RotatingFileHandler",
                "maxBytes": s.rotate_bytes,
                "backupCount": s.backups,
                "filename": str(s.file_path),
                "formatter": formatter_key,
                "encoding": "utf-8",
                "filters": ["omp_filter"],
            }
        if s.rotate_when:
            return {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "when": s.rotate_when,
                "backupCount": s.backups,
                "filename": str(s.file_path),
                "formatter": formatter_key,
                "encoding": "utf-8",
                "filters": ["omp_filter"],
            }
        return {
            "class": "logging.FileHandler",
            "filename": str(s.file_path),
            "formatter": formatter_key,
            "encoding": "utf-8",
            "filters": ["omp_filter"],
        }
    """Modular builder for project-wide logging configuration."""

    def __init__(self, settings: Optional[LogSettings] = None):
        self.settings = settings or LogSettings()
        # persistent queue instance for QueueHandler/Listener pairing
        self._queue = queue.Queue() if self.settings.use_queue else None

    # ----- Legacy-args bridge -----
    def apply_legacy_args(
        self,
        *,
        log_level,
        log_filepath,
        max_log_file_size,
        backup_count,
        console,
    ) -> None:
        s = self.settings
        s.level = (logging.getLevelName(log_level) if isinstance(log_level, int) else str(log_level)).upper()
        if console is False:
            s.to_stdout = False
            s.to_file = True
        if log_filepath != DEFAULT_LOG_FILEPATH:
            s.to_file = True
            s.file_path = BASE_LOG_DIR / Path(log_filepath)
        if max_log_file_size and max_log_file_size != MAX_FILE_SIZE:
            s.rotate_bytes = int(max_log_file_size)
        s.backups = backup_count or s.backups

    # ----- Builders -----
    def build_formatters(self) -> dict:
        s = self.settings
        fmts: dict[str, dict] = {}
        if s.json_format and JsonFormatter is not None:
            fmts["json"] = {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "fmt": LOG_FMT_JSON,
                "json_ensure_ascii": False,
            }
        else:
            fmts["plain"] = {
                "()": f"{__name__}.UtcFormatter",
                "fmt": LOG_FMT_PLAIN,
            }
            if s.is_dev() and colorlog and s.should_color():
                fmts["color"] = {
                    "()": "colorlog.ColoredFormatter",
                    "format": LOG_FMT_COLOR,
                    "log_colors": LOG_COLORS,
                }
        return fmts

    def build_filters(self) -> dict:
        return {"omp_filter": {"()": f"{__name__}.OMPFilter"}}

    def build_handlers(self, formatters: dict) -> dict:
        s = self.settings
        handlers: dict[str, dict] = {}

        # stdout handler
        if s.to_stdout:
            if s.json_format and JsonFormatter is not None:
                fmt = "json"
            elif s.is_dev() and colorlog and s.should_color():
                fmt = "color"
            else:
                fmt = "plain"
            handlers["stdout"] = self._stdout_handler_config(fmt)

        # file handler
        formatter_key = "json" if (s.json_format and JsonFormatter is not None) else "plain"
        if s.to_file:
            handlers["file"] = self._file_handler_config(formatter_key=formatter_key)

        # queue wrapper
        if s.use_queue and handlers:
            if self._queue is None:
                self._queue = queue.Queue()
            handlers["queue"] = {
                "class": "logging.handlers.QueueHandler",
                "queue": self._queue,
            }
        return handlers
    
    # ----- Private helpers (queue sinks) -----
    def _make_stream_sink(self) -> logging.Handler:
        s = self.settings
        sh = logging.StreamHandler(self.settings.selected_stream())
        if s.json_format and JsonFormatter is not None:
            sh.setFormatter(JsonFormatter(LOG_FMT_JSON))
        elif s.is_dev() and colorlog and s.should_color():
            sh.setFormatter(colorlog.ColoredFormatter(LOG_FMT_COLOR, log_colors=LOG_COLORS))
        else:
            sh.setFormatter(UtcFormatter(LOG_FMT_PLAIN))
        sh.addFilter(OMPFilter())
        return sh

    def _make_file_sink(self) -> logging.Handler:
        s = self.settings
        if s.rotate_bytes:
            fh: logging.Handler = RotatingFileHandler(
                str(s.file_path),
                maxBytes=s.rotate_bytes,
                backupCount=s.backups,
                encoding="utf-8",
            )
        elif s.rotate_when:
            fh = TimedRotatingFileHandler(
                str(s.file_path),
                when=s.rotate_when,
                backupCount=s.backups,
                encoding="utf-8",
            )
        else:
            fh = logging.FileHandler(str(s.file_path), encoding="utf-8")

        if s.json_format and JsonFormatter is not None:
            fh.setFormatter(JsonFormatter(LOG_FMT_JSON))
        else:
            fh.setFormatter(UtcFormatter(LOG_FMT_PLAIN))
        fh.addFilter(OMPFilter())
        return fh

    def select_base_handlers(self, handlers: dict) -> list[str]:
        s = self.settings
        base_handlers: list[str] = []
        if s.use_queue and ("queue" in handlers):
            base_handlers.append("queue")
        else:
            if "stdout" in handlers:
                base_handlers.append("stdout")
            if "file" in handlers:
                base_handlers.append("file")
        return base_handlers

    def build_config(self, *, filters: dict, formatters: dict, handlers: dict) -> dict:
        s = self.settings
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": filters,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": {
                s.base_name: {
                    "level": s.level,
                    "handlers": self.select_base_handlers(handlers),
                    "propagate": False,
                }
            },
        }

    def apply_config(self, config: dict) -> None:
        logging.config.dictConfig(config)
        logging.captureWarnings(self.settings.capture_warnings)
        # When routing Python warnings into logging, the records go to 'py.warnings'.
        # Attach our base handlers so warnings are visible.
        if self.settings.capture_warnings:
            base = logging.getLogger(self.settings.base_name)
            pyw = logging.getLogger("py.warnings")
            # Avoid duplicate handlers on re-configure
            existing = {id(h) for h in pyw.handlers}
            for h in base.handlers:
                if id(h) not in existing:
                    pyw.addHandler(h)
            # Ensure records are emitted even if root has no handlers
            pyw.setLevel(logging.WARNING)
            pyw.propagate = False

    def start_queue_listener(self, handlers: dict) -> None:
        global _queue_listener
        s = self.settings
        if not (s.use_queue and ("queue" in handlers)):
            return
        q_logger = logging.getLogger(s.base_name)
        qh = next((h for h in q_logger.handlers if isinstance(h, QueueHandler)), None)
        if qh is None:
            return
        q = qh.queue  # type: ignore[attr-defined]

        sink_handlers: list[logging.Handler] = []
        if "stdout" in handlers:
            sink_handlers.append(self._make_stream_sink())
        if "file" in handlers and s.to_file:
            sink_handlers.append(self._make_file_sink())

        if _queue_listener:
            with contextlib.suppress(Exception):
                _queue_listener.stop()
        _queue_listener = QueueListener(q, *sink_handlers, respect_handler_level=True)
        _queue_listener.start()

    def suppress_noise(self, modules_override, force: bool = False) -> None:
        s = self.settings
        modules = modules_override
        # Normalize to a list of module names (strings)
        if modules is None:
            modules = s.suppress_modules  # env string by default
        if isinstance(modules, str):
            modules_list = [m.strip() for m in modules.split(",") if m.strip()]
        else:
            # Attempt to iterate; if not iterable, coerce to single-item list
            try:
                modules_list = [str(m).strip() for m in modules if str(m).strip()]
            except TypeError:
                modules_list = [str(modules).strip()] if str(modules).strip() else []
        for module in modules_list:
            logger = logging.getLogger(module)
            if force or logger.level == logging.NOTSET:
                logger.setLevel(logging.WARNING)

    # ----- Facade -----
    def configure(
        self,
        *,
        legacy_args: dict,
        suppressed_modules,
    ) -> logging.Logger:
        self.apply_legacy_args(**legacy_args)
        formatters = self.build_formatters()
        filters = self.build_filters()
        handlers = self.build_handlers(formatters)
        config = self.build_config(filters=filters, formatters=formatters, handlers=handlers)
        self.apply_config(config)
        self.start_queue_listener(handlers)
        self.suppress_noise(suppressed_modules, force=False)
        return logging.getLogger(self.settings.base_name)


def setup_logging(
    log_level=logging.INFO,
    log_filepath=DEFAULT_LOG_FILEPATH,
    max_log_file_size=MAX_FILE_SIZE,  # 10MB
    backup_count=5,
    console=True,
    suppressed_modules=None,
    *,
    settings: "LogSettings|None" = None,
) -> logging.Logger:
    """
    Initialize project-wide logging using dictConfig, with JSON in prod and colorized/plain text in dev.

    Backward compatible with previous signature. Prefer using env vars or pass a LogSettings via the
    keyword-only `settings` parameter.
    """
    global _queue_listener
    configurator = LoggingConfigurator(settings=settings)
    legacy_args = {
        "log_level": log_level,
        "log_filepath": log_filepath,
        "max_log_file_size": max_log_file_size,
        "backup_count": backup_count,
        "console": console,
    }
    return configurator.configure(legacy_args=legacy_args, suppressed_modules=suppressed_modules)


class OMPFilter(logging.Filter):
    def filter(self, record):
        # Suppress messages containing "OMP:"
        return "OMP:" not in record.getMessage()


def get_child_logger(name: str, console: bool = False, separate_file: bool = False) -> logging.Logger:
    """
    Get a child logger that writes logs to a console or a specified file.

    Args:
        name (str): The name of the child logger (e.g., module name).
        console (bool, optional): If True, log to the console. If False, do not log to the console.
                                  If None, inherit console behavior from the parent logger.

    Returns:
        logging.Logger: Configured child logger.
    """
    
    def _setup_logfile(name, logger):
        logfile = BASE_LOG_DIR / f"{name}.log"
        logfile.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        file_handler = RotatingFileHandler(
            filename=str(logfile),
            maxBytes=MAX_FILE_SIZE,  # Use the global MAX_FILE_SIZE
            backupCount=5,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter(DEFAULT_FILE_FORMAT_STRING)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Create the fully qualified child logger name
    full_name = f"{BASE_LOG_NAME}.{name}"
    logger = logging.getLogger(full_name)

    # Check if the logger already has handlers to avoid duplication
    if not logger.handlers:
        # Add console handler if specified
        if console:
            console_handler = colorlog.StreamHandler()
            console_formatter = colorlog.ColoredFormatter(
                DEFAULT_CONSOLE_FORMAT_STRING,
                log_colors=LOG_COLORS,
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # Add file handler if a file path is provided
        if separate_file:
            _setup_logfile(name, logger)
        # Prevent duplication if we've attached custom handlers
        logger.propagate = not console and not separate_file

    return logger

# --- Compatibility shims for gradual migration ---

def get_logger(name: str) -> logging.Logger:
    """Preferred helper: returns a namespaced logger under the base project name.

    Backwards-compatible with existing call sites that used get_child_logger(__name__).
    """
    return logging.getLogger(f"{BASE_LOG_NAME}.{name}")


def setup_logging_legacy(*args, **kwargs) -> logging.Logger:
    """Deprecated: use setup_logging().

    This wrapper preserves old call sites during migration. It emits a DeprecationWarning
    (once per process) and forwards all arguments to the current setup_logging().
    """
    warnings.warn(
        "setup_logging_legacy() is deprecated; migrate to setup_logging() and get_logger().",
        DeprecationWarning,
        stacklevel=2,
    )
    return setup_logging(*args, **kwargs)


# Export a clean public surface
__all__ = [
    "BASE_LOG_NAME",
    "BASE_LOG_DIR",
    "DEFAULT_LOG_FILEPATH",
    "MAX_FILE_SIZE",
    "OMPFilter",
    "setup_logging",
    "setup_logging_legacy",
    "get_logger",
    "get_child_logger",  # kept for backward compatibility
]
