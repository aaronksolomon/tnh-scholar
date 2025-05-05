from .ai_text_processing import (
    OpenAIProcessor,
    SectionParser,
    SectionProcessor,
    find_sections,
    get_pattern,
    process_text,
    process_text_by_paragraphs,
    process_text_by_sections,
)
from .line_translator import translate_text_by_lines
from .openai_process_interface import openai_process_text
from .patterns import (
    GitBackedRepository,
    LocalPatternManager,
    Pattern,
    PatternManager,
)
from .text_object import (
    AIResponse,
    LogicalSection,
    SectionEntry,
    TextObject,
    TextObjectInfo,
)

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
    "LocalPatternManager",
    "Pattern",
    "PatternManager",
    "AIResponse",
    "LogicalSection",
    "SectionEntry",
    "TextObject",
    "TextObjectInfo",
]