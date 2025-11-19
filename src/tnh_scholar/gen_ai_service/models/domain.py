"""Domain Models for GenAIService.

Contains immutable, semantically meaningful Pydantic models representing system behavior
(e.g., CompletionResult, RenderRequest, Message, Usage). These are used within
the service and never directly serialized to provider SDKs.

Connected modules:
  - models.transport.ProviderRequest / ProviderResponse
  - providers.base.ProviderClient
  - service.GenAIService

Policy note:
  ADR-A02 (V1 walking skeleton, now superseded by ADR-A12) assumes a simple precedence
  rule for model selection: an explicit `RenderRequest.model` overrides a prompt’s
  `model_hint`. This rule is
  currently implemented in code for V1 expedience. In later phases, this precedence
  MUST be governed by a configurable policy (e.g., a ModelSelectionPolicy) rather
  than being hard-coded here. Suggested location: `src/tnh_scholar/config/render_policy.py`
  with a minimal interface such as:
    - class ModelSelectionPolicy:
        def choose_model(self, explicit: str | None, hint: str | None) -> str | None: ...
  The GenAIService should delegate to this policy so that precedence can be changed
  via configuration without modifying domain models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from openai.types.chat.chat_completion_content_part_param import (
    ChatCompletionContentPartParam,
)
from pydantic import BaseModel

# V1 Requirement (ADR-A02) to avoid passing raw dicts
# later versions: move to a pydantic model
RenderVars = Dict[str, Any]


# Fingerprint domain model
class Fingerprint(BaseModel):
    schema_version: Literal["fp-1"] = "fp-1"
    prompt_key: str
    prompt_name: str
    prompt_base_path: str
    prompt_content_hash: str
    variables_hash: str
    user_string_hash: str

class CompletionParams(BaseModel):
    temperature: float = 0.2
    max_output_tokens: int = 512
    seed: Optional[int] = None
    model: Optional[str] = None
    provider: Optional[str] = None

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
class CompletionResult(BaseModel):
    text: str
    usage: Usage | None
    model: str
    provider: str
    parsed: BaseModel | None = None
    
class Provenance(BaseModel):
    provider: str
    model: str
    sdk_version: str | None = None
    started_at: datetime
    finished_at: datetime
    attempt_count: int = 1
    fingerprint: Fingerprint

class CompletionEnvelope(BaseModel):
    result: CompletionResult
    provenance: Provenance
    policy_applied: dict
    warnings: list[str] = []
    
class Role(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    
class Message(BaseModel):
    role: Role
    # content can be plain text or a list of content-part objects supported by
    # the OpenAI SDK (ChatCompletionContentPartParam) for richer responses
    content: Union[str, List[ChatCompletionContentPartParam]]

class RenderRequest(BaseModel):
    instruction_key: str
    user_input: str                      # verbatim caller input
    variables: RenderVars | None = None   # template variables for rendering
    intent: str | None = None
    # V1 rule (ADR-A12): explicit request overrides prompt hint.
    # Future: this rule to be owned by config-driven ModelSelectionPolicy.
    model: str | None = None           # explicit model override (takes precedence over prompt model_hint)

class RenderedPrompt(BaseModel):
    system: Optional[str]
    messages: List[Message]
