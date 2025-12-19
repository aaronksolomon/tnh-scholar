"""Issue Handler.

Centralized runtime issue handler for configuration and runtime issue handling and validation.
Provides static helper methods (e.g., `no_api_key()`) that emit warnings/logs and/or handle exceptions
during initialization and running of GenAIService module.

Connected modules:
  - service.GenAIService
  - models.errors.ConfigurationError
  - config.settings
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.logging_config import get_logger
from tnh_scholar.utils.file_utils import ensure_directory_writable


class IssueHandler:
    """
    Centralized issue handler for configuration and runtime validation.

    Provides static helper methods (e.g., `no_api_key()`) that emit warnings,
    raise structured exceptions, and optionally terminate execution when
    critical configuration or runtime conditions are not met.

    Usage:
        if not settings.openai_api_key:
            IssueHandler.no_api_key("OPENAI_API_KEY")

    Connected modules:
        - service.GenAIService
        - models.errors.ConfigurationError
        - config.settings
    """

    logger = get_logger("tnh_scholar.gen_ai_service")

    @staticmethod
    def no_api_key(env_var: str, exit_on_fail: bool = False) -> None:
        """
        Handles missing API key configuration.

        Args:
            env_var (str): The name of the environment variable expected.
            exit_on_fail (bool): Whether to terminate the program after handling.
                                 Defaults to False (raises exception instead).
                                 Only CLI entry points should pass True.

        Raises:
            ConfigurationError: When the required API key is missing and
                                exit_on_fail is False.
        """
        message = f"Missing required API key: {env_var}. Please set this environment variable."

        IssueHandler.logger.error(message)

        if exit_on_fail:
            sys.stderr.write(f"\n[CRITICAL] {message}\n")
            sys.exit(1)

        # Raise a structured exception (default behavior for library usage)
        raise ConfigurationError(message)

    @staticmethod
    def no_prompt_catalog() -> Path:
        """
        Fallback handler for missing prompt catalog directory.

        V1 walking‑skeleton behavior:
        - Emit a warning.
        - Create (if not exists) a ./gen_ai_prompts directory in the current working dir.
        - Return the path for use by PromptsAdapter.
        """
        cwd = Path(os.getcwd())
        fallback = cwd / "gen_ai_prompts"

        IssueHandler.logger.warning(
            f"No prompt catalog configured. Using fallback directory: {fallback}"
        )

        # Create directory if needed
        # Will raise if cannot create writeable directory
        ensure_directory_writable(fallback)
        
        return fallback
    
    @staticmethod
    def warn(message: str) -> None:
        """Emit a runtime warning without raising."""
        IssueHandler.logger.warning(message)

    @staticmethod
    def info(message: str) -> None:
        """Log an informational message."""
        IssueHandler.logger.info(message)

    @staticmethod
    def handle_exception(exc: Exception, context: Optional[str] = None) -> None:
        """
        Generic exception handler for unhandled runtime errors.
        """
        IssueHandler.logger.exception(f"Unhandled exception: {exc!r} | Context: {context or 'N/A'}")
