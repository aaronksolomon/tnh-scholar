"""
Public surface for ``tnh_scholar.ai_text_processing``.

Historically this module eagerly imported multiple submodules with heavy
dependencies (e.g., audio codecs, ML toolkits) which made importing lightweight
components such as ``Prompt`` surprisingly expensive and brittle in test
environments.  We now lazily import the concrete implementations on demand so
that callers can depend on just the pieces they need.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "OpenAIProcessor",
    "SectionParser",
    "SectionProcessor",
    "find_sections",
    "process_text",
    "process_text_by_paragraphs",
    "process_text_by_sections",
    "get_pattern",
    "translate_text_by_lines",
    "openai_process_text",
    "GitBackedRepository",
    "LocalPromptManager",
    "Prompt",
    "PromptCatalog",
    "AIResponse",
    "LogicalSection",
    "SectionEntry",
    "TextObject",
    "TextObjectInfo",
]

_LAZY_ATTRS = {
    # ai_text_processing.py
    "OpenAIProcessor": "tnh_scholar.ai_text_processing.ai_text_processing",
    "SectionParser": "tnh_scholar.ai_text_processing.ai_text_processing",
    "SectionProcessor": "tnh_scholar.ai_text_processing.ai_text_processing",
    "find_sections": "tnh_scholar.ai_text_processing.ai_text_processing",
    "process_text": "tnh_scholar.ai_text_processing.ai_text_processing",
    "process_text_by_paragraphs": "tnh_scholar.ai_text_processing.ai_text_processing",
    "process_text_by_sections": "tnh_scholar.ai_text_processing.ai_text_processing",
    "get_pattern": "tnh_scholar.ai_text_processing.ai_text_processing",
    # lightweight helpers
    "translate_text_by_lines": "tnh_scholar.ai_text_processing.line_translator",
    "openai_process_text": "tnh_scholar.ai_text_processing.openai_process_interface",
    # prompt system
    "GitBackedRepository": "tnh_scholar.ai_text_processing.prompts",
    "LocalPromptManager": "tnh_scholar.ai_text_processing.prompts",
    "Prompt": "tnh_scholar.ai_text_processing.prompts",
    "PromptCatalog": "tnh_scholar.ai_text_processing.prompts",
    # text object models
    "AIResponse": "tnh_scholar.ai_text_processing.text_object",
    "LogicalSection": "tnh_scholar.ai_text_processing.text_object",
    "SectionEntry": "tnh_scholar.ai_text_processing.text_object",
    "TextObject": "tnh_scholar.ai_text_processing.text_object",
    "TextObjectInfo": "tnh_scholar.ai_text_processing.text_object",
}


def __getattr__(name: str) -> Any:
    module_path = _LAZY_ATTRS.get(name)
    if not module_path:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_path)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)


if TYPE_CHECKING:  # pragma: no cover
    from .ai_text_processing import (  # noqa: F401
        OpenAIProcessor,
        SectionParser,
        SectionProcessor,
        find_sections,
        get_pattern,
        process_text,
        process_text_by_paragraphs,
        process_text_by_sections,
    )
    from .line_translator import translate_text_by_lines  # noqa: F401
    from .openai_process_interface import openai_process_text  # noqa: F401
    from .prompts import (  # noqa: F401
        GitBackedRepository,
        LocalPromptManager,
        Prompt,
        PromptCatalog,
    )
    from .text_object import (  # noqa: F401
        AIResponse,
        LogicalSection,
        SectionEntry,
        TextObject,
        TextObjectInfo,
    )
