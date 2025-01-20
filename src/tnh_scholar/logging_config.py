import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog

BASE_LOG_NAME = "tnh"  # tnh-scholar project
BASE_LOG_DIR = Path("./logs")
DEFAULT_LOG_FILEPATH = Path("main.log")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 mb

# Define custom log level: PRIORITY_INFO
PRIORITY_INFO_LEVEL = 25
logging.addLevelName(PRIORITY_INFO_LEVEL, "PRIORITY_INFO")


def priority_info(self, message, *args, **kwargs):
    if self.isEnabledFor(PRIORITY_INFO_LEVEL):
        self._log(PRIORITY_INFO_LEVEL, message, args, **kwargs)


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

# Default format strings
DEFAULT_CONSOLE_FORMAT_STRING = (
    "%(asctime)s - %(name)s - %(log_color)s%(levelname)s%(reset)s - %(message)s"
)
DEFAULT_FILE_FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class OMPFilter(logging.Filter):
    def filter(self, record):
        # Suppress messages containing "OMP:"
        return "OMP:" not in record.getMessage()


def setup_logging(
    log_level=logging.INFO,
    log_filepath=DEFAULT_LOG_FILEPATH,
    max_log_file_size=MAX_FILE_SIZE,  # 10MB
    backup_count=5,
    console_format=DEFAULT_CONSOLE_FORMAT_STRING,
    file_format=DEFAULT_FILE_FORMAT_STRING,
    console=True,
    suppressed_modules=None,
):
    """
    Configure the base logger with handlers, including the custom PRIORITY_INFO level.

    Args:
        log_level (int): Logging level for the base logger.
        log_file_path (Path): Path to the log file.
        max_log_file_size (int): Maximum log file size in bytes.
        backup_count (int): Number of backup log files to keep.
        console_format (str): Format string for console logs.
        file_format (str): Format string for file logs.
        suppressed_modules (list): List of third-party modules to suppress logs for.
    """
    # Create the base logger
    log_file_path = BASE_LOG_DIR / log_filepath
    base_logger = logging.getLogger(BASE_LOG_NAME)
    base_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplication
    base_logger.handlers.clear()

    # Colorized console handler
    if console:
        console_handler = colorlog.StreamHandler()
        console_formatter = colorlog.ColoredFormatter(
            console_format,
            log_colors=LOG_COLORS,
        )
        console_handler.setFormatter(console_formatter)
        # Add the OMP filter to the console handler
        console_handler.addFilter(OMPFilter())
        base_logger.addHandler(console_handler)

    # Plain file handler
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_log_file_size,
        backupCount=backup_count,
    )
    file_formatter = logging.Formatter(file_format)
    file_handler.setFormatter(file_formatter)
    base_logger.addHandler(file_handler)

    # Suppress noisy third-party logs
    if suppressed_modules:
        for module in suppressed_modules:
            logging.getLogger(module).setLevel(logging.WARNING)

    # Prevent propagation to the root logger
    base_logger.propagate = False

    return base_logger


def get_child_logger(name: str, console: bool = None, separate_file: bool = False):
    """
    Get a child logger that writes logs to a console or a specified file.

    Args:
        name (str): The name of the child logger (e.g., module name).
        console (bool, optional): If True, log to the console. If False, do not log to the console.
                                  If None, inherit console behavior from the parent logger.
        file (Path, optional): A string specifying a logfile to log to. will be placed under existing root logs directory. If provided,
                               a rotating file handler will be added.

    Returns:
        logging.Logger: Configured child logger.
    """
    # Create the fully qualified child logger name
    full_name = f"{BASE_LOG_NAME}.{name}"
    logger = logging.getLogger(full_name)
    logger.debug(f"Created logger with name: {logger.name}")

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
            logfile = BASE_LOG_DIR / f"{name}.log"
            logfile.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
            file_handler = RotatingFileHandler(
                filename=logfile,
                maxBytes=MAX_FILE_SIZE,  # Use the global MAX_FILE_SIZE
                backupCount=5,
            )
            file_formatter = logging.Formatter(DEFAULT_FILE_FORMAT_STRING)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Ensure the logger inherits handlers and settings from the base logger
        logger.propagate = True

    return logger
