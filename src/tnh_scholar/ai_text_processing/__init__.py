from .patterns import (
    Pattern,
    GitBackedRepository,
    PatternManager,
)

from .openai_process_interface import (
    openai_process_text
)

from .ai_text_processing import (
    OpenAIProcessor,
    SectionParser, 
    SectionProcessor,
    find_sections,
    process_text_by_sections,
    process_text_by_paragraphs,
    process_text, 
    punctuate_text,
    translate_text_by_lines,
   
)

from .response_format import (
    LogicalSection,
    TextObject
)

from .lang import (
    get_language_code,
    get_language_name,
    get_language_from_code
)