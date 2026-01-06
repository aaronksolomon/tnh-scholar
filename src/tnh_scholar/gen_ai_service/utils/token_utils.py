"""Token counting utilities for GenAI service.

Provides consistent token counting across different models and use cases.
Uses tiktoken for accurate token estimation matching OpenAI's behavior.

Connected modules:
  - gen_ai_service.models.domain (Message)
  - External: tiktoken, openai
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Mapping, Protocol, Union, cast

try:
    import tiktoken as _tiktoken
except ModuleNotFoundError:  # pragma: no cover - fallback path
    _tiktoken = None

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    import tiktoken
else:
    tiktoken = _tiktoken

from openai.types.chat.chat_completion_content_part_param import (
    ChatCompletionContentPartParam,
)

from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.gen_ai_service.config.registry import find_model_info
from tnh_scholar.gen_ai_service.models.domain import Message
from tnh_scholar.logging_config import get_logger
from tnh_scholar.utils.file_utils import read_str_from_file

logger = get_logger("tnh_scholar.gen_ai_service.utils.token_utils")

# Default model for token counting when not specified
DEFAULT_TOKEN_MODEL = "gpt-4o"


class _EncodingLike(Protocol):
    """Protocol representing the subset of encoding behavior we need."""

    def encode(self, text: str) -> list[int]: ...


class _FallbackEncoding:
    """Lightweight, deterministic encoding when tiktoken isn't available."""

    def encode(self, text: str) -> list[int]:
        return [ord(char) for char in text] if text else []


@dataclass(frozen=True)
class FormattingPolicy:
    """Formatting overhead for chat messages."""

    tokens_per_message: int
    base_tokens: int
    tokens_per_name: int


@dataclass(frozen=True)
class BufferPolicy:
    """Reserve space for completions."""

    ratio: float
    minimum: int


@dataclass(frozen=True)
class EncodingFallbackPolicy:
    """Fallback mapping for models missing in tiktoken."""

    long_context_threshold: int
    long_context_encoding: str
    default_encoding: str


FormattingPolicyEntry = tuple[str, FormattingPolicy]
MessageContent = Union[str, Sequence[ChatCompletionContentPartParam]]
MessageSequence = Sequence[Message]


MESSAGE_FORMATTING_POLICIES: tuple[FormattingPolicyEntry, ...] = (
    ("gpt-5", FormattingPolicy(tokens_per_message=3, base_tokens=3, tokens_per_name=1)),
    ("gpt-4", FormattingPolicy(tokens_per_message=3, base_tokens=3, tokens_per_name=1)),
    ("gpt-3.5", FormattingPolicy(tokens_per_message=3, base_tokens=3, tokens_per_name=1)),
)
DEFAULT_FORMATTING_POLICY = FormattingPolicy(tokens_per_message=4, base_tokens=3, tokens_per_name=1)

FALLBACK_CONTEXT_LIMIT = 8_192
DEFAULT_BUFFER_POLICY = BufferPolicy(ratio=0.01, minimum=256)


class EncodingProvider:
    """Caches encodings and falls back when tiktoken is unavailable."""

    def __init__(self, policy: EncodingFallbackPolicy | None = None) -> None:
        self._cache: dict[str, _EncodingLike] = {}
        self._fallback_warning_emitted = False
        self._fallback_encoding = _FallbackEncoding()
        self._policy = policy or EncodingFallbackPolicy(
            long_context_threshold=128000,
            long_context_encoding="o200k_base",
            default_encoding="cl100k_base",
        )

    def count_text(self, text: str, model: str) -> int:
        if not text:
            return 0
        encoding = self.get_encoding(model)
        return len(encoding.encode(text))

    def get_encoding(self, model: str) -> _EncodingLike:
        encoding = self._cache.get(model)
        if encoding is not None:
            return encoding

        if tiktoken is None:
            if not self._fallback_warning_emitted:
                logger.warning(
                    "tiktoken not installed; falling back to character-count token estimation"
                )
                self._fallback_warning_emitted = True
            self._cache[model] = self._fallback_encoding
            return self._fallback_encoding

        try:
            resolved = tiktoken.encoding_for_model(model)
        except KeyError:
            resolved = self._resolve_registry_encoding(model)
            if resolved is None:
                logger.warning(
                    "Unknown model '%s' for token counting, falling back to %s encoding",
                    model,
                    self._policy.default_encoding,
                )
                try:
                    resolved = tiktoken.get_encoding(self._policy.default_encoding)
                except Exception as exc:
                    logger.warning(
                        "Failed to load %s encoding, using fallback: %s",
                        self._policy.default_encoding,
                        exc,
                    )
                    self._cache[model] = self._fallback_encoding
                    return self._fallback_encoding
        except Exception as exc:
            logger.warning(
                "Failed to resolve encoding for model '%s', using fallback: %s",
                model,
                exc,
            )
            self._cache[model] = self._fallback_encoding
            return self._fallback_encoding

        self._cache[model] = resolved
        return resolved

    def _resolve_registry_encoding(self, model: str) -> _EncodingLike | None:
        try:
            model_info = find_model_info(model)
        except ConfigurationError:
            return None

        encoding_name = self._encoding_name_for_context(int(model_info.context_window))
        try:
            return tiktoken.get_encoding(encoding_name)
        except Exception as exc:
            logger.warning(
                "Failed to resolve encoding '%s' for model '%s', using fallback: %s",
                encoding_name,
                model,
                exc,
            )
            return None

    def _encoding_name_for_context(self, context_window: int) -> str:
        if context_window >= self._policy.long_context_threshold:
            return self._policy.long_context_encoding
        return self._policy.default_encoding


class MessageContentRenderer:
    """Converts structured message content into deterministic text."""

    def render(self, content: MessageContent) -> str:
        return content if isinstance(content, str) else self._render_sequence(content)

    def _render_sequence(self, parts: Sequence[ChatCompletionContentPartParam]) -> str:
        rendered_parts = [self._render_part(part) for part in parts]
        return "\n".join(part for part in rendered_parts if part)

    def _render_part(self, part: ChatCompletionContentPartParam) -> str:
        part_data = cast(Mapping[str, object], part)
        part_type = part_data.get("type")

        match part_type:
            case "text":
                return self._render_text_part(part_data)
            case "image_url":
                return self._render_image_part(part_data)
            case "input_audio":
                return self._render_audio_part(part_data)
            case "file":
                return self._render_file_part(part_data)
            case _:
                return self._render_unknown_part(part)

    def _render_text_part(self, part_data: Mapping[str, object]) -> str:
        text_value = part_data.get("text")
        return text_value if isinstance(text_value, str) else ""

    def _render_image_part(self, part_data: Mapping[str, object]) -> str:
        image_url = part_data.get("image_url")
        if isinstance(image_url, Mapping):
            url = image_url.get("url")
            detail = image_url.get("detail")
            url_text = url if isinstance(url, str) else ""
            detail_text = f" detail={detail}" if isinstance(detail, str) else ""
            if descriptor := f"{url_text}{detail_text}".strip():
                return f"[image_url {descriptor}]"
        return "[image_url]"

    def _render_audio_part(self, part_data: Mapping[str, object]) -> str:
        audio = part_data.get("input_audio")
        if isinstance(audio, Mapping):
            fmt = audio.get("format")
            data = audio.get("data")
            fmt_text = fmt if isinstance(fmt, str) else "audio"
            size_hint = f" {len(data)}b" if isinstance(data, str) else ""
            return f"[input_audio {fmt_text}{size_hint}]"
        return "[input_audio]"

    def _render_file_part(self, part_data: Mapping[str, object]) -> str:
        file_info = part_data.get("file")
        if isinstance(file_info, Mapping):
            filename = file_info.get("filename")
            file_id = file_info.get("file_id")
            descriptor = filename or file_id
            if isinstance(descriptor, str) and descriptor:
                return f"[file {descriptor}]"
        return "[file]"

    def _render_unknown_part(self, part: ChatCompletionContentPartParam) -> str:
        return str(part)


class ModelPolicyRegistry:
    """Resolves formatting and context policies for models."""

    def __init__(
        self,
        *,
        context_limit_resolver: "ContextLimitResolver",
        formatting_entries: Sequence[FormattingPolicyEntry],
    ) -> None:
        self._context_limit_resolver = context_limit_resolver
        self._formatting_entries = tuple(formatting_entries)

    def formatting_policy(self, model: str) -> FormattingPolicy:
        return next(
            (
                policy
                for prefix, policy in self._formatting_entries
                if model.startswith(prefix)
            ),
            DEFAULT_FORMATTING_POLICY,
        )

    def context_limit(self, model: str, override: int | None) -> int:
        if override is not None:
            return override
        return self._context_limit_resolver.resolve(model)


class ContextLimitResolver(Protocol):
    """Resolves context limits for models."""

    def resolve(self, model: str) -> int:
        """Resolve a context limit for a model."""


class RegistryContextLimitResolver:
    """Resolves context limits from the provider registry."""

    def __init__(self, fallback_limit: int) -> None:
        self._fallback_limit = fallback_limit

    def resolve(self, model: str) -> int:
        try:
            model_info = find_model_info(model)
            return int(model_info.context_window)
        except ConfigurationError:
            logger.warning(
                "Unknown context limit for model '%s', assuming %s tokens",
                model,
                self._fallback_limit,
            )
            return self._fallback_limit


class MessageTokenCounter:
    """Counts tokens for chat message sequences."""

    def __init__(
        self,
        *,
        encoding_provider: EncodingProvider,
        renderer: MessageContentRenderer,
        policy_registry: ModelPolicyRegistry,
    ) -> None:
        self._encoding_provider = encoding_provider
        self._renderer = renderer
        self._policies = policy_registry

    def count(self, messages: MessageSequence, model: str) -> int:
        if not messages:
            return 0

        encoding = self._encoding_provider.get_encoding(model)
        policy = self._policies.formatting_policy(model)
        num_tokens = policy.base_tokens

        for message in messages:
            num_tokens += policy.tokens_per_message
            num_tokens += self._count_content_tokens(message, encoding)
            num_tokens += len(encoding.encode(self._role_text(message)))
            num_tokens += self._count_name_tokens(message, encoding, policy.tokens_per_name)

        return num_tokens

    def _count_content_tokens(self, message: Message, encoding: _EncodingLike) -> int:
        if not message.content:
            return 0
        normalized = self._renderer.render(message.content)
        return len(encoding.encode(normalized))

    def _role_text(self, message: Message) -> str:
        return str(message.role)

    def _count_name_tokens(
        self,
        message: Message,
        encoding: _EncodingLike,
        tokens_per_name: int,
    ) -> int:
        name = getattr(message, "name", None)
        if not isinstance(name, str) or not name:
            return 0
        return tokens_per_name + len(encoding.encode(name))


class CompletionBudgetEstimator:
    """Determines remaining completion tokens for a prompt."""

    def __init__(
        self,
        *,
        policy_registry: ModelPolicyRegistry,
        buffer_policy: BufferPolicy,
    ) -> None:
        self._policy_registry = policy_registry
        self._buffer_policy = buffer_policy

    def estimate(self, prompt_tokens: int, model: str, context_limit: int | None) -> int:
        if prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")

        limit = self._policy_registry.context_limit(model, context_limit)
        remaining = limit - prompt_tokens
        if remaining <= 0:
            raise ValueError(
                f"Prompt ({prompt_tokens} tokens) exceeds or nearly exceeds "
                f"model context limit ({limit} tokens)"
            )

        buffer = max(
            int(remaining * self._buffer_policy.ratio),
            self._buffer_policy.minimum,
        )
        max_tokens = remaining - buffer

        if max_tokens <= 0:
            raise ValueError(
                f"Prompt ({prompt_tokens} tokens) exceeds or nearly exceeds "
                f"model context limit ({limit} tokens)"
            )

        return max_tokens


_encoding_provider = EncodingProvider()
_content_renderer = MessageContentRenderer()
_policy_registry = ModelPolicyRegistry(
    context_limit_resolver=RegistryContextLimitResolver(FALLBACK_CONTEXT_LIMIT),
    formatting_entries=MESSAGE_FORMATTING_POLICIES,
)
_message_counter = MessageTokenCounter(
    encoding_provider=_encoding_provider,
    renderer=_content_renderer,
    policy_registry=_policy_registry,
)
_completion_estimator = CompletionBudgetEstimator(
    policy_registry=_policy_registry,
    buffer_policy=DEFAULT_BUFFER_POLICY,
)


def token_count(text: str, model: str = DEFAULT_TOKEN_MODEL) -> int:
    """
    Count tokens in a text string.

    Args:
        text: Text to count tokens in
        model: Model to use for encoding (default: gpt-4o)

    Returns:
        int: Number of tokens in the text
    """
    return _encoding_provider.count_text(text, model)


def token_count_file(file_path: Union[str, Path], model: str = DEFAULT_TOKEN_MODEL) -> int:
    """
    Count tokens in a text file.

    Args:
        file_path: Path to text file
        model: Model to use for encoding (default: gpt-4o)

    Returns:
        int: Number of tokens in the file

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    text = read_str_from_file(path)
    return token_count(text, model=model)


def token_count_messages(messages: MessageSequence, model: str = DEFAULT_TOKEN_MODEL) -> int:
    """
    Count tokens in a list of messages, accounting for message formatting overhead.
    """
    return _message_counter.count(messages, model)


def estimate_max_completion_tokens(
    prompt_tokens: int,
    model: str = DEFAULT_TOKEN_MODEL,
    context_limit: int | None = None,
) -> int:
    """
    Estimate maximum completion tokens given prompt size.
    """
    return _completion_estimator.estimate(prompt_tokens, model, context_limit)


__all__ = [
    "token_count",
    "token_count_file",
    "token_count_messages",
    "estimate_max_completion_tokens",
]
