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
  - Pinned OpenAI SDK: 2.15.0 (see PINNED_OPENAI_SDK below)
  - Reference: openai/types/chat/chat_completion.py and openai/types/chat/chat_completion_message_param.py 
   (SDK 2.5.0)
  - This module defines the provider seam → canonical transport envelope.

TODOs for Hardening:
  - Add telemetry for unknown finish_reason and schema drift (infra.metrics/infra.tracer).
  - Add compatibility matrix doc (docs/providers/openai_adapter.md) and link to it from here.
  - Add automated version drift check against latest OpenAI SDK to flag mapping review.
  - Add guardrails for empty choices / malformed usage with structured FAILED status.
  - Revalidate request/response shapes after the OpenAI SDK 2.15.0 bump.
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
    AdapterDiagnostics,
    FinishReason,
    FailureReason,
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
    ProviderUsage,
    TextPayload,
)

ADAPTER_COMPAT_VERSION = "2025-10-31"
PINNED_OPENAI_SDK = "2.15.0"


class OpenAIChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessageParam]
    temperature: float
    max_completion_tokens: int
    seed: Optional[int] = None
    response_format: Optional[type[BaseModel]] = None


def _finish_reason_from_raw(raw_finish_reason: Any) -> FinishReason:
    if isinstance(raw_finish_reason, str):
        finish_reason_map = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
            "tool_calls": FinishReason.TOOL_CALLS,
            "function_call": FinishReason.FUNCTION_CALL,
            "null": FinishReason.OTHER,
        }
        return finish_reason_map.get(raw_finish_reason, FinishReason.OTHER)
    return FinishReason.OTHER


def _content_from_message(message: Any) -> tuple[str | None, int | None]:
    content = getattr(message, "content", None)
    if content is None:
        return None, None
    if isinstance(content, str):
        return content, None
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            part_type = None
            part_text = None
            if isinstance(part, dict):
                part_type = part.get("type")
                part_text = part.get("text")
            else:
                part_type = getattr(part, "type", None)
                part_text = getattr(part, "text", None)
            if part_type == "text" and part_text is not None:
                parts.append(str(part_text))
        return "".join(parts), len(content)
    return None, None


def _failed_response(
    *,
    provider: str,
    model: str,
    attempts: int,
    usage: ProviderUsage | None,
    failure_reason: FailureReason,
    content_source: str,
    content_part_count: int | None,
    raw_finish_reason: str | None,
    extraction_notes: str,
) -> ProviderResponse:
    return ProviderResponse(
        provider=provider,
        model=model,
        status=ProviderStatus.FAILED,
        attempts=attempts,
        payload=None,
        usage=usage,
        failure_reason=failure_reason,
        adapter_diagnostics=AdapterDiagnostics(
            content_source=content_source,
            content_part_count=content_part_count,
            raw_finish_reason=raw_finish_reason,
            extraction_notes=extraction_notes,
        ),
    )


def _provider_usage_from_response_usage(usage_obj: Any) -> ProviderUsage:
    prompt_tokens = getattr(usage_obj, "prompt_tokens", None)
    completion_tokens = getattr(usage_obj, "completion_tokens", None)
    total_tokens = getattr(usage_obj, "total_tokens", None)
    provider_breakdown = usage_obj.dict() if hasattr(usage_obj, "dict") else {}
    return ProviderUsage(
        tokens_in=prompt_tokens,
        tokens_out=completion_tokens,
        tokens_total=total_tokens,
        provider_breakdown=provider_breakdown,
    )


def _validate_response_structure(
    response: ChatCompletion,
    *,
    provider: str,
    model: str,
    attempts: int,
) -> tuple[Any, Any] | ProviderResponse:
    choices = getattr(response, "choices", None)
    if not choices:
        return _failed_response(
            provider=provider,
            model=model,
            attempts=attempts,
            usage=None,
            failure_reason=FailureReason.UNSUPPORTED_RESPONSE_SHAPE,
            content_source="choices[0].message.content",
            content_part_count=None,
            raw_finish_reason=None,
            extraction_notes="response.choices was empty",
        )

    choice = choices[0]
    message = getattr(choice, "message", None)
    if message is None:
        return _failed_response(
            provider=provider,
            model=model,
            attempts=attempts,
            usage=None,
            failure_reason=FailureReason.UNSUPPORTED_RESPONSE_SHAPE,
            content_source="choices[0].message.content",
            content_part_count=None,
            raw_finish_reason=str(getattr(choice, "finish_reason", None)),
            extraction_notes="choices[0].message was missing",
        )
    return choice, message


def _usage_from_openai_response(response: ChatCompletion) -> tuple[ProviderStatus, str | None, ProviderUsage | None, int | None]:
    usage_obj = getattr(response, "usage", None)
    if usage_obj is None:
        return ProviderStatus.INCOMPLETE, "missing usage metadata", None, None

    prompt_tokens = getattr(usage_obj, "prompt_tokens", None)
    completion_tokens = getattr(usage_obj, "completion_tokens", None)
    provider_usage = _provider_usage_from_response_usage(usage_obj)
    if prompt_tokens is None or completion_tokens is None:
        return (
            ProviderStatus.INCOMPLETE,
            "partial usage metadata: missing prompt_tokens or completion_tokens",
            provider_usage,
            completion_tokens,
        )
    return ProviderStatus.OK, None, provider_usage, completion_tokens


def _raw_content_missing(message: Any) -> bool:
    raw_content = getattr(message, "content", None)
    return raw_content is None or raw_content == ""


def _content_failure_response(
    *,
    provider: str,
    model: str,
    attempts: int,
    usage: ProviderUsage | None,
    content_part_count: int | None,
    raw_finish_reason: Any,
    failure_reason: FailureReason,
    extraction_notes: str,
) -> ProviderResponse:
    return _failed_response(
        provider=provider,
        model=model,
        attempts=attempts,
        usage=usage,
        failure_reason=failure_reason,
        content_source="choices[0].message.content",
        content_part_count=content_part_count,
        raw_finish_reason=str(raw_finish_reason) if raw_finish_reason is not None else None,
        extraction_notes=extraction_notes,
    )


def _extract_content_and_finish_reason(
    *,
    message: Any,
    choice: Any,
    provider: str,
    model: str,
    attempts: int,
    usage: ProviderUsage | None,
    completion_tokens: int | None,
) -> tuple[TextPayload, ProviderStatus, str | None] | ProviderResponse:
    raw_finish_reason = getattr(choice, "finish_reason", None)
    text, content_part_count = _content_from_message(message)
    parsed_obj = getattr(message, "parsed", None)
    parsed_value = parsed_obj if isinstance(parsed_obj, BaseModel) else None
    if parsed_value is not None:
        return (
            TextPayload(
                text=text or "",
                finish_reason=_finish_reason_from_raw(raw_finish_reason),
                parsed=parsed_value,
            ),
            ProviderStatus.OK if usage is not None else ProviderStatus.INCOMPLETE,
            None if usage is not None else "missing usage metadata",
        )

    if text is None:
        return _content_failure_response(
            provider=provider,
            model=model,
            attempts=attempts,
            usage=usage,
            content_part_count=content_part_count,
            raw_finish_reason=raw_finish_reason,
            failure_reason=FailureReason.CONTENT_FIELD_MISSING,
            extraction_notes="message.content was missing",
        )

    if text != "":
        return (
            TextPayload(
                text=text,
                finish_reason=_finish_reason_from_raw(raw_finish_reason),
                parsed=None,
            ),
            ProviderStatus.OK if usage is not None else ProviderStatus.INCOMPLETE,
            None if usage is not None else "missing usage metadata",
        )

    if completion_tokens is not None and completion_tokens > 0:
        return _content_failure_response(
            provider=provider,
            model=model,
            attempts=attempts,
            usage=usage,
            content_part_count=content_part_count,
            raw_finish_reason=raw_finish_reason,
            failure_reason=FailureReason.EMPTY_CONTENT_WITH_TOKENS,
            extraction_notes=f"message.content was empty; completion_tokens={completion_tokens}",
        )

    if _raw_content_missing(message):
        return _content_failure_response(
            provider=provider,
            model=model,
            attempts=attempts,
            usage=usage,
            content_part_count=content_part_count,
            raw_finish_reason=raw_finish_reason,
            failure_reason=FailureReason.CONTENT_FIELD_MISSING,
            extraction_notes="message.content was empty with no completion tokens",
        )

    return _content_failure_response(
        provider=provider,
        model=model,
        attempts=attempts,
        usage=usage,
        content_part_count=content_part_count,
        raw_finish_reason=raw_finish_reason,
        failure_reason=FailureReason.UNSUPPORTED_RESPONSE_SHAPE,
        extraction_notes=f"unsupported content type: {type(getattr(message, 'content', None)).__name__}",
    )


def _build_success_response(
    *,
    provider: str,
    model: str,
    attempts: int,
    payload: TextPayload,
    status: ProviderStatus,
    usage: ProviderUsage | None,
    incomplete_reason: str | None,
) -> ProviderResponse:
    return ProviderResponse(
        provider=provider,
        model=model,
        status=status,
        attempts=attempts,
        payload=payload,
        usage=usage,
        incomplete_reason=incomplete_reason,
    )


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
        
        try:
            structure = _validate_response_structure(
                response,
                provider=provider,
                model=model,
                attempts=attempts,
            )
            if isinstance(structure, ProviderResponse):
                return structure

            choice, message = structure
            status, incomplete_reason, provider_usage, completion_tokens = _usage_from_openai_response(
                response
            )
            extracted = _extract_content_and_finish_reason(
                message=message,
                choice=choice,
                provider=provider,
                model=model,
                attempts=attempts,
                usage=provider_usage,
                completion_tokens=completion_tokens,
            )
            if isinstance(extracted, ProviderResponse):
                return extracted

            payload, _, _ = extracted
            return _build_success_response(
                provider=provider,
                model=model,
                attempts=attempts,
                payload=payload,
                status=status,
                usage=provider_usage,
                incomplete_reason=incomplete_reason,
            )
        except Exception as exc:
            raw_usage = getattr(response, "usage", None)
            provider_usage = (
                _provider_usage_from_response_usage(raw_usage)
                if raw_usage is not None
                else None
            )
            return _failed_response(
                provider=provider,
                model=model,
                attempts=attempts,
                usage=provider_usage,
                failure_reason=FailureReason.CONTENT_EXTRACTION_ERROR,
                content_source="choices[0].message.content",
                content_part_count=None,
                raw_finish_reason=None,
                extraction_notes=str(exc),
            )


# 🔒 Compatibility Checklist (update when bumping OpenAI SDK or models):
# [ ] Update finish_reason_map if new reasons appear
# [ ] Add/adjust guards for choices/usage schema drift
# [ ] Re-run golden tests and update fixtures
# [ ] Update docs/providers/openai_adapter.md with any deltas
# [ ] Bump ADAPTER_COMPAT_VERSION and note changes in CHANGELOG
