import logging
import colorlog
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, List, Dict, Any

class LoggingConfig:
    """
    A container for logging configuration parameters.
    """

    def __init__(
        self,
        base_logger_name: str = "base",
        log_level: int = logging.INFO,
        console_enabled: bool = True,
        log_file_path: Optional[Path] = None,
        max_log_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_format: str = "%(asctime)s - %(name)s - {log_color}%(levelname)s{reset} - %(message)s",
        file_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        custom_log_levels: Optional[Dict[str, int]] = None,
        suppressed_modules: Optional[List[str]] = None,
        log_colors: Optional[Dict[str, str]] = None,
    ):
        self.base_logger_name = base_logger_name
        self.log_level = log_level
        self.console_enabled = console_enabled
        self.log_file_path = log_file_path
        self.max_log_file_size = max_log_file_size
        self.backup_count = backup_count
        self.console_format = console_format
        self.file_format = file_format
        self.custom_log_levels = custom_log_levels or {}
        self.suppressed_modules = suppressed_modules or []
        self.log_colors = log_colors or {
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }
        self.initialized = False

    def _setup_logger(self, logger: logging.Logger):
        """
        Set up the handlers and formatters for a given logger based on the configuration.

        Args:
            logger (logging.Logger): The logger to configure.
        """
        # Clear any existing handlers to avoid duplication
        logger.handlers.clear()

        # Set the log level
        logger.setLevel(self.log_level)

        # Add console handler if enabled
        if self.console_enabled:
            console_handler = logging.StreamHandler()
            console_formatter = colorlog.ColoredFormatter(
                self.console_format, log_colors=self.log_colors
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # Add file handler if a log file path is provided
        if self.log_file_path:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
            file_handler = RotatingFileHandler(
                filename=self.log_file_path,
                maxBytes=self.max_log_file_size,
                backupCount=self.backup_count,
            )
            file_formatter = logging.Formatter(self.file_format)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Suppress specific modules if configured
        for module in self.suppressed_modules:
            logging.getLogger(module).setLevel(logging.WARNING)

        # Add custom log levels
        for level_name, level_value in self.custom_log_levels.items():
            logging.addLevelName(level_value, level_name.upper())

            def custom_level(self, message, *args, **kwargs):
                if self.isEnabledFor(level_value):
                    self._log(level_value, message, args, **kwargs)

            setattr(logging.Logger, level_name.lower(), custom_level)

        # Ensure propagation is enabled to allow messages to propagate to parent loggers
        logger.propagate = True

    def validate(self):
        """Validate configuration parameters."""
        if self.log_file_path and not isinstance(self.log_file_path, Path):
            raise ValueError("log_file_path must be a pathlib.Path object or None.")
        if not isinstance(self.log_level, int):
            raise ValueError("log_level must be an integer.")
        # Additional validation logic as needed

    def to_dict(self):
        """Convert the configuration to a dictionary."""
        return self.__dict__

    @staticmethod
    def from_dict(config: dict):
        """Create a LoggingConfig instance from a dictionary."""
        return LoggingConfig(**config)

    def update(self, params: Dict[str, Any]):
        """Update configuration values dynamically."""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_console_enabled(self) -> bool:
        """Check if console logging is enabled."""
        return self.console_enabled

    def is_file_logging_enabled(self) -> bool:
        """Check if file logging is enabled."""
        return self.log_file_path is not None
    
def initialize(config: LoggingConfig):
    """
    Initialize the global logging configuration.
    """
    global _LOGGING_CONFIG
    _LOGGING_CONFIG = config
    _LOGGING_CONFIG.initialized = True

def initialize(config: LoggingConfig):
    """
    Initialize the root logger with custom handlers and formatters.
    Configures the root logger based on the LoggingConfig instance.

    Args:
        config (LoggingConfig): The configuration instance.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level)

    # Clear any existing handlers to avoid duplication
    root_logger.handlers.clear()

    # Set up console handler
    if config.console_enabled:
        console_handler = logging.StreamHandler()
        console_formatter = colorlog.ColoredFormatter(
            config.console_format, log_colors=config.log_colors
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Set up file handler if a log file path is provided
    if config.log_file_path:
        config.log_file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        file_handler = RotatingFileHandler(
            filename=config.log_file_path,
            maxBytes=config.max_log_file_size,
            backupCount=config.backup_count,
        )
        file_formatter = logging.Formatter(config.file_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Suppress specific modules
    for module in config.suppressed_modules:
        logging.getLogger(module).setLevel(logging.WARNING)

    # Ensure propagation is enabled for child loggers
    root_logger.propagate = True

def getLogger(name: str) -> logging.Logger:
    """
    Get a logger by name. If LoggingConfig has not been initialized,
    fall back to the default logging behavior.

    Args:
        name (str): Name of the logger.

    Returns:
        logging.Logger: Configured logger or default logger.
    """
    global _LOGGING_CONFIG

    if _LOGGING_CONFIG is None or not _LOGGING_CONFIG.initialized:
        # Fallback to default logging behavior
        return logging.getLogger(name)

    # For now, simply return logging.getLogger()
    # This will be expanded in future iterations
    return logging.getLogger(name)
