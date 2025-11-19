"""Transport Models for Provider I/O.

Defines intermediate models exchanged across the ProviderClient protocol boundary.
These map closely to SDK request/response payloads while maintaining strong typing.

Connected modules:
  - providers.*_adapter
  - models.domain
  - ports.genai_port
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from .domain import Message


class ProviderName(str):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ProviderRequest(BaseModel):
    provider: str
    model: str
    messages: List[Message]
    system: Optional[str] = None
    temperature: float
    max_output_tokens: int
    seed: Optional[int] = None
    response_format: Optional[Type[BaseModel]] = None

class ProviderStatus(str, Enum):
    OK = "ok"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
    FILTERED = "filtered"
    RATE_LIMITED = "rate_limited"

class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    TOOL_CALLS = "tool_calls"
    FUNCTION_CALL = "function_call"
    OTHER = "other"

class ErrorKind(str, Enum):
    PROVIDER = "provider"
    TIMEOUT = "timeout"
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    SAFETY = "safety"
    UNKNOWN = "unknown"

class ErrorInfo(BaseModel):
    kind: ErrorKind
    message: str
    code: Optional[str] = None
    retry_after_s: Optional[float] = None

class ProviderUsage(BaseModel):
    """Transport-level usage (provider-agnostic, not domain)."""
    tokens_in: Optional[int] = None          # aka prompt/input tokens
    tokens_out: Optional[int] = None         # aka completion/output tokens
    tokens_total: Optional[int] = None       # adapters may compute
    # Optional multi-modal counters — fill only if provider reports them
    chars_in: Optional[int] = None
    chars_out: Optional[int] = None
    images_in: Optional[int] = None
    audio_seconds_in: Optional[float] = None
    # Raw provider details for auditing/future mapping
    provider_breakdown: Dict[str, Any] = {}

class TextPayload(BaseModel):
    text: str
    finish_reason: Optional[FinishReason] = None
    parsed: Optional[BaseModel] = None

class ProviderResponse(BaseModel):
    """Normalized provider response.

    - `usage` may be None when the provider did not include usage metadata.
    - `incomplete` signals that some expected metadata was missing or could
      not be parsed; `incomplete_reason` provides a short explanation. This
      allows higher layers to decide whether to treat the response as
      acceptable or to retry/fail.
    """
    provider: str
    model: str
    status: ProviderStatus = ProviderStatus.OK
    attempts: int = 1
    payload: Optional[TextPayload] = None
    usage: Optional[ProviderUsage] = None
    error: Optional[ErrorInfo] = None
    incomplete_reason: Optional[str] = None
    
