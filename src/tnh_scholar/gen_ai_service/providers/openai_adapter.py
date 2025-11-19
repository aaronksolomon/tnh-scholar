"""OpenAI Adapter.

Implements ProviderClient for OpenAI's ChatCompletion API.
Responsible for converting ProviderRequest → SDK request
and SDK response → ProviderResponse via OpenAIMapper.

Connected modules:
  - providers/base.ProviderClient
  - models/transport
  - models/domain
  - infra.metrics, infra.tracer

Compatibility:
  - Pinned OpenAI SDK: 2.5.0 (see PINNED_OPENAI_SDK below)
  - Reference: openai/types/chat/chat_completion.py and openai/types/chat/chat_completion_message_param.py 
   (SDK 2.5.0)
  - This module defines the provider seam → canonical transport envelope.

TODOs for Hardening:
  - Add telemetry for unknown finish_reason and schema drift (infra.metrics/infra.tracer).
  - Add compatibility matrix doc (docs/providers/openai_adapter.md) and link to it from here.
  - Add automated version drift check against latest OpenAI SDK to flag mapping review.
  - Add guardrails for empty choices / malformed usage with structured FAILED status.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_message_param import (
    ChatCompletionMessageParam,
)
from pydantic import BaseModel

from tnh_scholar.gen_ai_service.models.domain import Message
from tnh_scholar.gen_ai_service.models.transport import (
    FinishReason,
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
    ProviderUsage,
    TextPayload,
)

ADAPTER_COMPAT_VERSION = "2025-10-31"
PINNED_OPENAI_SDK = "2.5.0"


class OpenAIChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessageParam]
    temperature: float
    max_completion_tokens: int
    seed: Optional[int] = None
    response_format: Optional[type[BaseModel]] = None


class OpenAIAdapter:
    def _to_message_param(self, msg: Message) -> Dict[str, Any]:
        """Return a plain dict that matches one of the OpenAI ChatCompletion message
        TypedDict shapes. We avoid per-branch casting here and instead cast once
        in `to_openai_request` when assembling the final request.

        msg.content may be a str or a list of ChatCompletionContentPartParam.
        """
        role = msg.role.value
        base = {"role": role, "content": msg.content}

        # include name only when present
        if (name := getattr(msg, "name", None)):
            base["name"] = name

        return base
        

    def to_openai_request(self, req: ProviderRequest) -> OpenAIChatCompletionRequest:
        """
        Build OpenAI ChatCompletion request payload from ProviderRequest.

        Purpose
        -------
        Request-side seam: our transport → OpenAI SDK typed request.

        Inputs
        ------
        req : ProviderRequest
            - model, temperature, max_output_tokens, seed
            - system: Optional[str]
            - messages: List[domain.Message] (content may be str or list of content parts)

        Outputs
        -------
        OpenAIChatCompletionRequest
            Typed pydantic model mirroring required OpenAI fields.

        Invariants
        ----------
        - We cast the assembled message list once to OpenAI's `ChatCompletionMessageParam` union.
        - We do not import provider SDK types earlier than this seam.
        - Future changes to roles/content shapes should be handled here.

        References
        ----------
        - OpenAI Chat Completions request schema (pinned SDK: 2.5.0)
        - ADR §8.8 Internal Layer Adapters

        TODOs
        -----
        - Add request schema guardrails if OpenAI introduces new message shapes.
        - Add compatibility matrix entry for request-side fields when docs are created.
        """
        
        # NOTE: We cast message dicts into ChatCompletionMessageParam
        #   as defined in openai/types/chat/chat_completion_message_param.py:
        #   expects fields {"role": str, "content": str | list, "name": Optional[str]}.
        raw_msgs: List[Dict[str, Any]] = []
        if req.system:
            raw_msgs.append({"role": "system", "content": req.system})
        raw_msgs.extend(self._to_message_param(m) for m in req.messages)

        # Cast once to the OpenAI typed union for the boundary
        messages = cast(List[ChatCompletionMessageParam], raw_msgs)

        return OpenAIChatCompletionRequest(
            model=req.model,
            messages=messages,
            temperature=req.temperature,
            max_completion_tokens=req.max_output_tokens,
            seed=req.seed,
            response_format=req.response_format,
        )

    def from_openai_response(
        self, 
        response: ChatCompletion, 
        *, 
        model: str, 
        provider: str,
        attempts: int,
        ) -> ProviderResponse:
        """
        Map OpenAI ChatCompletion → ProviderResponse (transport envelope).

        Purpose
        -------
        Response-side seam: OpenAI SDK schema → our canonical envelope.

        Inputs
        ------
        response: openai.types.chat.ChatCompletion
            Expected fields used here:
              - choices[0].message.content: str | None
              - choices[0].finish_reason: str | None
              - usage: object | None with prompt_tokens, completion_tokens, total_tokens
        model: the model descriptor string
        provider: the provider id string 
        attempts: the number of attempts made to generate the response

        Outputs
        -------
        ProviderResponse
            - status: OK or INCOMPLETE (usage missing/partial)
            - payload: TextPayload(text, finish_reason)
            - usage: ProviderUsage | None
            - incomplete_reason: Optional[str]

        Invariants
        ----------
        - Unknown finish_reason maps to FinishReason.OTHER.
        - No domain imports; this is purely transport-facing.
        - Infra failures (auth/network) should be raised by the client, not handled here.

        References
        ----------
        - OpenAI SDK pinned: 2.5.0 (see PINNED_OPENAI_SDK)
        - Adapter compat version: 2025-10-31 (ADAPTER_COMPAT_VERSION)
        - ADR §8.8 Internal Layer Adapters

        Future TODOs (Hardening)
        ------------------------
        - Emit telemetry on unknown finish_reason / missing choices (infra.metrics/tracer).
        - Add FAILED status mapping for empty choices or malformed payloads.
        - Document mapping matrix in docs/providers/openai_adapter.md and keep golden tests.
        - Add automated version drift check to flag re-validation when SDK updates.
        """
        
        # Finish reason mapping:
        # OpenAI → our FinishReason. Unknown values MUST map to OTHER.
        # When adding new mapping, update docs/providers/openai_adapter.md and tests.
        finish_reason_map = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
            "tool_calls": FinishReason.TOOL_CALLS,
            "function_call": FinishReason.FUNCTION_CALL,
            "null": FinishReason.OTHER,
        }
        raw_finish_reason = getattr(response.choices[0], "finish_reason", None)
        if isinstance(raw_finish_reason, str):
            finish_reason = finish_reason_map.get(raw_finish_reason, FinishReason.OTHER)
        else:
            finish_reason = FinishReason.OTHER

        # NOTE: We access choices[0].message.content.
        #   - ChatCompletion.choices is guaranteed non-empty for successful completions,
        #     per openai/types/chat/chat_completion.py (v2.5.0).
        #   - For safety, future hardening may add a guard for empty choices.
        message = response.choices[0].message
        text = message.content or ""
        parsed_obj = getattr(message, "parsed", None)
        parsed_value = parsed_obj if isinstance(parsed_obj, BaseModel) else None

        u = getattr(response, "usage", None)
        provider_usage = None
        status = ProviderStatus.OK
        incomplete_reason = None
        if u is not None:
            prompt_tokens = getattr(u, "prompt_tokens", None)
            completion_tokens = getattr(u, "completion_tokens", None)
            total_tokens = getattr(u, "total_tokens", None)
            provider_breakdown = u.dict() if hasattr(u, "dict") else {}
            provider_usage = ProviderUsage(
                tokens_in=prompt_tokens,
                tokens_out=completion_tokens,
                tokens_total=total_tokens,
                provider_breakdown=provider_breakdown,
            )
            if prompt_tokens is None or completion_tokens is None:
                status = ProviderStatus.INCOMPLETE
                incomplete_reason = "partial usage metadata: missing prompt_tokens or completion_tokens"
        else:
            status = ProviderStatus.INCOMPLETE
            incomplete_reason = "missing usage metadata"

        return ProviderResponse(
            provider=provider,
            model=model,
            status=status,
            attempts=attempts,
            payload=TextPayload(
                text=text,
                finish_reason=finish_reason,
                parsed=parsed_value,
            ),
            usage=provider_usage,
            incomplete_reason=incomplete_reason,
        )


# 🔒 Compatibility Checklist (update when bumping OpenAI SDK or models):
# [ ] Update finish_reason_map if new reasons appear
# [ ] Add/adjust guards for choices/usage schema drift
# [ ] Re-run golden tests and update fixtures
# [ ] Update docs/providers/openai_adapter.md with any deltas
# [ ] Bump ADAPTER_COMPAT_VERSION and note changes in CHANGELOG
