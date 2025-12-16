from __future__ import annotations

import json
from enum import IntEnum
from typing import Any, Tuple

from click.exceptions import BadParameter

from tnh_scholar.exceptions import (
    ConfigurationError,
    ExternalServiceError,
    RateLimitError,
    ValidationError,
)
from tnh_scholar.gen_ai_service.models.errors import ProviderError


class ExitCode(IntEnum):
    SUCCESS = 0
    POLICY_ERROR = 1
    TRANSPORT_ERROR = 2
    PROVIDER_ERROR = 3
    FORMAT_ERROR = 4
    INPUT_ERROR = 5


def map_exception(exc: Exception) -> ExitCode:
    if isinstance(exc, ValidationError):
        return ExitCode.POLICY_ERROR
    if isinstance(exc, (ExternalServiceError, ConnectionError, TimeoutError)):
        return ExitCode.TRANSPORT_ERROR
    if isinstance(exc, (ProviderError, RateLimitError)):
        return ExitCode.PROVIDER_ERROR
    if isinstance(exc, (json.JSONDecodeError,)):
        return ExitCode.FORMAT_ERROR
    if isinstance(exc, (ConfigurationError, BadParameter, FileNotFoundError, KeyError, ValueError)):
        return ExitCode.INPUT_ERROR
    return ExitCode.PROVIDER_ERROR


def error_response(
    exc: Exception,
    *,
    error_code: str | None = None,
    suggestion: str | None = None,
    correlation_id: str,
) -> Tuple[dict[str, Any], ExitCode]:
    exit_code = map_exception(exc)
    diagnostics: dict[str, Any] = {
        "error_type": exc.__class__.__name__,
        "error_code": error_code or exc.__class__.__name__.upper(),
    }
    if suggestion:
        diagnostics["suggestion"] = suggestion

    payload = {
        "status": "failed",
        "error": str(exc) or exc.__class__.__name__,
        "diagnostics": diagnostics,
        "correlation_id": correlation_id,
    }
    return payload, exit_code
