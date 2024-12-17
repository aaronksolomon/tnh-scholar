import logging
import colorlog
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, List, Dict

# Global variable for the base logger name
BASE_LOGGER_NAME = None
UNINITIALIZED_LOGGERS = {}  # Stores loggers created before initialization

LOG_COLORS = {
    "DEBUG": "blue",
    "INFO": "green",
    "PRIORITY_INFO": "bold_yellow",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

DEFAULT_CONSOL_FORMAT_STRING = "%(asctime)s - %(name)s - {log_color}%(levelname)s{reset} - %(message)s"
DEFAULT_FILE_FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Define custom log level: PRIORITY_INFO
PRIORITY_INFO_LEVEL = 25
logging.addLevelName(PRIORITY_INFO_LEVEL, "PRIORITY_INFO")

def priority_info(self, message, *args, **kwargs):
    if self.isEnabledFor(PRIORITY_INFO_LEVEL):
        self._log(PRIORITY_INFO_LEVEL, message, args, **kwargs)

setattr(logging.Logger, "priority_info", priority_info)

LOG_COLORS["PRIORITY_INFO"] = "bold_yellow"

# Add PRIORITY_INFO to the Logger class
setattr(logging.Logger, "priority_info", priority_info)

def initialize(
    name: str = 'base',
    log_file_path: Optional[Path] = None,
    log_level: int = logging.INFO,
    console: bool = True,
    format_string: str = DEFAULT_FILE_FORMAT_STRING,
    console_format_string: str = DEFAULT_CONSOL_FORMAT_STRING,
    suppressed_modules: Optional[List[str]] = None,
    custom_levels: Optional[Dict[str, int]] = None,
):
    """
    Initializes the base logger for the project.
    Also updates any uninitialized loggers created before this function was called.
    """
    global BASE_LOGGER_NAME, UNINITIALIZED_LOGGERS
    BASE_LOGGER_NAME = name

    # Create or retrieve the base logger
    logger = logging.getLogger(name)
    logger.handlers.clear()  # Clear existing handlers to avoid duplicates
    logger.setLevel(log_level)

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_formatter = colorlog.ColoredFormatter(
            console_format_string, log_colors=LOG_COLORS
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file_path:
        log_file_path = Path(log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)

    # Suppress noisy modules
    if suppressed_modules:
        for module in suppressed_modules:
            logging.getLogger(module).setLevel(logging.WARNING)

    # Register custom levels
    if custom_levels:
        for level_name, level_value in custom_levels.items():
            logging.addLevelName(level_value, level_name.upper())

            def custom_level(self, message, *args, **kwargs):
                if self.isEnabledFor(level_value):
                    self._log(level_value, message, args, **kwargs)

            setattr(logging.Logger, level_name.lower(), custom_level)

    logger.propagate = True  # Ensure propagation to parent loggers

    # Update uninitialized loggers
    for child_logger_name in UNINITIALIZED_LOGGERS:
        child_logger = logging.getLogger(child_logger_name)
        for handler in logger.handlers:
            # Ensure no duplicate handlers
            if not any(isinstance(h, handler.__class__) for h in child_logger.handlers):
                child_logger.addHandler(handler)
        child_logger.setLevel(log_level)

    # Clear the uninitialized loggers registry
    UNINITIALIZED_LOGGERS.clear()

    return logger

def getLogger(
    name: str,
    log_file_path: Optional[Path] = None,
    log_level: Optional[int] = None,
    console: Optional[bool] = None,  
) -> logging.Logger:
    """
    Retrieves or creates a child logger under the base logger hierarchy.
    If `initialize` has not been called, the logger will be registered for later configuration.

    Args:
        name (str): Name of the child logger.
        log_file_path (Optional[Path]): Log file specific to this child logger.
        log_level (Optional[int]): Log level for this child logger (overrides the base logger's level if set).
        console (Optional[bool]): Whether to add a console handler for this child logger. If None, it inherits the base logger's behavior.

    Returns:
        logging.Logger: The configured child logger.
    """
    global BASE_LOGGER_NAME, UNINITIALIZED_LOGGERS

    # Determine the full logger name
    full_name = f"{BASE_LOGGER_NAME}.{name}" if BASE_LOGGER_NAME else name

    # Get the logger
    logger = logging.getLogger(full_name)

    # If `initialize` hasn't been called
    if not BASE_LOGGER_NAME:
        if full_name not in UNINITIALIZED_LOGGERS:
            UNINITIALIZED_LOGGERS[full_name] = True
        if not logger.handlers:
            # Add a NullHandler to prevent "No handlers could be found" warnings
            logger.addHandler(logging.NullHandler())

    # If `initialize` has been called
    else:
        # Add the appropriate handlers
        base_logger = logging.getLogger(BASE_LOGGER_NAME)

        # Inherit handlers from the base logger
        for handler in base_logger.handlers:
            if not any(isinstance(h, handler.__class__) for h in logger.handlers):
                logger.addHandler(handler)

        # Add a file handler for this child logger if `log_file_path` is provided
        if log_file_path:
            log_file_path = Path(log_file_path)  # Ensure it's a Path object
            if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == str(log_file_path) for h in logger.handlers):
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = RotatingFileHandler(
                    log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
                )
                file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)

        # Add a console handler for this child logger if specified
        if console is not None:
            if console:
                # Check if a console handler already exists
                if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
                    console_handler = logging.StreamHandler()
                    console_formatter = colorlog.ColoredFormatter(
                        "%(asctime)s - %(name)s - {log_color}%(levelname)s{reset} - %(message)s",
                        log_colors=LOG_COLORS,
                    )
                    console_handler.setFormatter(console_formatter)
                    logger.addHandler(console_handler)
            else:
                # Remove existing console handlers if console=False
                logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.StreamHandler)]

        # Override log level if specified
        if log_level is not None:
            logger.setLevel(log_level)

    logger.propagate = True  # Ensure logs propagate to the parent logger
    return logger


# # Define the custom PRIORITY_INFO level
# PRIORITY_INFO_LEVEL = 25  # Between INFO (20) and WARNING (30)
# logging.addLevelName(PRIORITY_INFO_LEVEL, "PRIORITY_INFO")

# def priority_info(self, message, *args, **kwargs):
#     """
#     Log 'PRIORITY_INFO' messages with bright yellow text for console logs.
#     """
#     if self.isEnabledFor(PRIORITY_INFO_LEVEL):
#         # Only add yellow formatting for console handlers
#         if any(isinstance(handler, logging.StreamHandler) for handler in self.handlers):
#             message = f"\033[93m{message}\033[0m"  # Bright yellow
#         self._log(PRIORITY_INFO_LEVEL, message, args, **kwargs)

# # Add the custom method to the Logger class
# setattr(Logger, "priority_info", priority_info)

# def initialize(
#     name: str = "base",  # Set a default parent logger name
#     log_file_path: Optional[Path] = None,  # Enforce Path object
#     log_level: int = logging.INFO,
#     console: bool = True,
#     format_string: Optional[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     console_format_string: Optional[str] = "%(asctime)s - %(name)s - \033[96m%(levelname)s\033[0m - %(message)s",
#     suppressed_modules: Optional[List[str]] = ["httpx", "urllib3", "httpcore"],
#     custom_levels: Optional[Dict[str, int]] = None
# ) -> Logger:
#     """
#     Configures and returns a parent logger instance with built-in PRIORITY_INFO support, 
#     custom log levels, colored console output, and file rotation capabilities.

#     This function provides a flexible logging utility, including a custom `PRIORITY_INFO` log level (displayed 
#     in yellow in the console) and optional file logging with rotation. It also allows suppression of logs 
#     from specific modules and the addition of custom log levels.

#     Args:
#         name (str): Name of the logger. Defaults to "my_project" (parent logger).
#         log_file_path (Path, optional): Path to the log file. If None, no file handler is added.
#         log_level (int): Default log level for the logger. Defaults to logging.INFO.
#         console (bool): Whether to enable console output. Defaults to True.
#         format_string (str, optional): Log message format for the file handler. Defaults to plain format.
#         console_format_string (str, optional): Log message format for the console. Defaults to colored format.
#         suppressed_modules (list, optional): List of module names to suppress lower-level logs. 
#             Defaults to ["httpx", "urllib3", "httpcore"]. Set to an empty list ([]) to disable suppression.
#         custom_levels (dict, optional): Dictionary of additional custom log levels to register.
#             e.g., {"TRACE": 15, "ALERT": 35}

#     Returns:
#         Logger: Configured parent logger instance with PRIORITY_INFO and other custom levels.

#     Example:
#         from pathlib import Path

#         if __name__ == "__main__":
#             logger = setup_logger(
#                 name="my_project",
#                 log_file_path=Path("./app.log"),
#                 log_level=logging.DEBUG,
#                 console=True,
#                 suppressed_modules=["httpx", "urllib3"],
#                 custom_levels={"TRACE": 15, "ALERT": 35}
#             )
#             logger.info("This is an info message.")
#             logger.priority_info("This is a priority info message.")
#             logger.debug("This is a debug message.")
#             logger.trace("This is a trace message.")
#             logger.alert("This is an alert message.")
#     """

#     # Create or retrieve the logger (default is "base" as the parent logger)
#     logger = logging.getLogger(name)
#     logger.handlers.clear()  # Clear existing handlers to avoid duplicates
#     logger.setLevel(log_level)

#     # Set up formatter for the console handler (colored text)
#     console_formatter = logging.Formatter(console_format_string)

#     # Add console handler
#     if console:
#         console_handler = logging.StreamHandler()
#         console_handler.setFormatter(console_formatter)
#         logger.addHandler(console_handler)

#     # Add file handler if specified
#     if log_file_path:
#         # Ensure parent directories exist
#         if isinstance(log_file_path, str):  # Convert string to Path if needed
#             log_file_path = Path(log_file_path)
#         log_file_path.parent.mkdir(parents=True, exist_ok=True)

#         file_handler = RotatingFileHandler(
#             log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
#         )
#         # Set up formatter for the file handler (plain text, no colors)
#         file_formatter = logging.Formatter(format_string)
#         file_handler.setFormatter(file_formatter)
#         logger.addHandler(file_handler)

#     # Suppress logs from specified modules
#     for module in suppressed_modules:
#         logging.getLogger(module).setLevel(logging.WARNING)

#     # Register additional custom log levels if provided
#     if custom_levels:
#         for level_name, level_value in custom_levels.items():
#             logging.addLevelName(level_value, level_name.upper())

#             def custom_level_method(self, message, *args, **kwargs):
#                 if self.isEnabledFor(level_value):
#                     self._log(level_value, message, args, **kwargs)

#             setattr(Logger, level_name.lower(), custom_level_method)

#     # Ensure child loggers propagate to this parent logger
#     logger.propagate = True

#     return logger

# def getLogger():
#     pass