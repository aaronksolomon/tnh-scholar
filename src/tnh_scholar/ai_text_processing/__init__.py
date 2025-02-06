from .ai_text_processing import (
    OpenAIProcessor,
    SectionParser,
    SectionProcessor,
    find_sections,
    process_text,
    process_text_by_paragraphs,
    process_text_by_sections,
    punctuate_text,
    translate_text_by_lines,
)
from .openai_process_interface import openai_process_text
from .patterns import (
    GitBackedRepository,
    Pattern,
    PatternManager,
)

from .text_object import (
    TextObject, 
    TextObjectInfo, 
    TextObjectResponse, 
    LogicalSection, 
    SectionEntry
)