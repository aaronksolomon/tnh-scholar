# external package imports
from typing import Dict, Optional

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.metadata.metadata import Metadata, ProcessMetadata
from tnh_scholar.text_processing import (
    NumberedText,
)
from tnh_scholar.utils.lang import (
    get_language_from_code,
)

from .ai_text_processing import (
    DEFAULT_REVIEW_COUNT,
    OpenAIProcessor,
    TextProcessor,
    _calculate_segment_size,
    get_pattern,
)
from .prompts import Prompt
from .text_object import TextObject

# internal package imports
logger = get_child_logger(__name__)

DEFAULT_TRANSLATE_STYLE = "'American Dharma Teaching'"
DEFAULT_TARGET_LANGUAGE = "en"
DEFAULT_TRANSLATION_PATTERN = "default_line_translate"
DEFAULT_TRANSLATE_CONTEXT_LINES = 3
DEFAULT_TRANSLATION_TARGET_TOKENS = 300
MIN_SEGMENT_SIZE = 4
MAX_RETRIES = 6
TRANSCRIPT_SEGMENT_MARKER = "TRANSCRIPT_SEGMENT"
PRECEDING_CONTEXT_MARKER = "PRECEDING_CONTEXT"
FOLLOWING_CONTEXT_MARKER = "FOLLOWING_CONTEXT"

class LineTranslator:
    """Translates text line by line while maintaining line numbers and context."""

    def __init__(
        self,
        processor: TextProcessor,
        pattern: Prompt,
        review_count: int = DEFAULT_REVIEW_COUNT,
        style: str = DEFAULT_TRANSLATE_STYLE,
        # Number of context lines before/after
        context_lines: int = DEFAULT_TRANSLATE_CONTEXT_LINES,  
    ):
        """
        Initialize line translator.

        Args:
            processor: Implementation of TextProcessor
            pattern: Pattern object containing translation instructions
            review_count: Number of review passes
            style: Translation style to apply
            context_lines: Number of context lines to include before/after
        """
        self.processor = processor
        self.pattern = pattern
        self.review_count = review_count
        self.style = style
        self.context_lines = context_lines

    def translate_segment(
        self,
        num_text: NumberedText,
        start_line: int,
        end_line: int,
        metadata: Metadata,
        target_language: str,
        source_language: str,
        template_dict: Optional[Dict] = None,
    ) -> str:
        """
        Translate a segment of text with context.

        Args:
            num_text: Numbered text to extract segment from
            start_line: Starting line number of segment
            end_line: Ending line number of segment
            metadata: metadata for text
            source_language: Source language code
            target_language: Target language code (default: en for English)
            template_dict: Optional additional template values

        Returns:
            Translated text segment with line numbers preserved
        """
        
        # Calculate context ranges
        preceding_start = max(1, start_line - self.context_lines)  # lines start on 1.
        following_end = min(num_text.end + 1, end_line + self.context_lines)

        # Extract context and segment
        preceding_context = num_text.get_numbered_segment(preceding_start, start_line)
        transcript_segment = num_text.get_numbered_segment(start_line, end_line)
        following_context = num_text.get_numbered_segment(end_line, following_end)

        # build input text
        translation_input = self._build_translation_input(
            preceding_context, transcript_segment, following_context
        )

        # Prepare template values
        template_values = {
            "source_language": get_language_from_code(source_language),
            "target_language": get_language_from_code(target_language),
            "review_count": self.review_count,
            "style": self.style,
            "metadata": metadata.to_yaml()
        }

        if template_dict:
            template_values |= template_dict

        # Get and apply translation instructions
        logger.info(f"Translating segment (lines {start_line}-{end_line})")
        translate_instructions = self.pattern.apply_template(template_values)

        if start_line <= 1:
            logger.debug(
                f"Translate instructions (first segment):\n{translate_instructions}"
            )
        logger.debug(f"Translation input:\n{translation_input}")
        
        return self._translate_with_retries(
            translation_input,
            translate_instructions,
            start_line,
            end_line,
            )

    def _translate_with_retries(
        self, 
        translation_input,
        translate_instructions, 
        start_line, end_line
        ) -> str:
        
        retries = 0
        translated_lines = ""

        while retries < MAX_RETRIES:
            translated_segment = self.processor.process_text(
                translation_input, translate_instructions)
            translated_lines = self._extract_lines(translated_segment)

            if not self._validate_lines(translated_lines, start_line, end_line):
                break  # Validation successful, exit loop

            retries += 1
            logger.warning(f"Validation failed for segment {start_line}-{end_line}, "
                           f"retrying (attempt {retries + 1}/{MAX_RETRIES})")
            # You might want to add a delay here, e.g., using time.sleep()

        if retries == MAX_RETRIES:
            logger.error(
                f"Validation failed after {MAX_RETRIES}"
                f" retries for segment {start_line}-{end_line}\n"
                "Using last generated result."
                )
        
        return self._extract_content(translated_lines)
            
    def _extract_content(self, lines: str) -> str:
        """convert line-numbered format to un-numbered text."""
        # clean each line and return full clean segment
        line_list = lines.splitlines()
        # Remove line numbering and strip whitespace
        stripped_lines = [line.split(':', 1)[-1].strip() for line in line_list]
        return "\n".join(stripped_lines)
        
            
    def _build_translation_input(
        self, preceding_context: str, transcript_segment: str, following_context: str
    ) -> str:
        """
        Build input text in required XML-style format.

        Args:
            preceding_context: Context lines before segment
            transcript_segment: Main segment to translate
            following_context: Context lines after segment

        Returns:
            Formatted input text
        """
        parts = []

        # Add preceding context if exists
        if preceding_context:
            parts.extend(
                [
                    PRECEDING_CONTEXT_MARKER,
                    preceding_context,
                    PRECEDING_CONTEXT_MARKER,
                    "",
                ]
            )

        # Add main segment (always required)
        parts.extend(
            [
                TRANSCRIPT_SEGMENT_MARKER,
                transcript_segment,
                TRANSCRIPT_SEGMENT_MARKER,
                "",
            ]
        )

        # Add following context if exists
        if following_context:
            parts.extend(
                [
                    FOLLOWING_CONTEXT_MARKER,
                    following_context,
                    FOLLOWING_CONTEXT_MARKER,
                    "",
                ]
            )

        return "\n".join(parts)

    def translate_text(
        self,
        text: TextObject,
        source_language: str,
        segment_size: Optional[int] = None,  
        target_language: str = DEFAULT_TARGET_LANGUAGE,
        template_dict: Optional[Dict] = None,
    ) -> TextObject:
        """
        Translate entire text in segments while maintaining line continuity.

        Args:
            text: Text to translate
            segment_size: Number of lines per translation segment
            source_language: Source language code
            target_language: Target language code (default: en for English)
            template_dict: Optional additional template values

        Returns:
            Complete translated text with line numbers preserved
        """
        
        # Use TextObject language if not specified
        if not source_language:
            source_language = text.language

        # Convert text to numbered lines
        num_text = text.num_text
        total_lines = num_text.size
        
        metadata = text.metadata

        if not segment_size:
            segment_size = _calculate_segment_size(
                num_text, DEFAULT_TRANSLATION_TARGET_TOKENS
            )

        translated_segments = []

        logger.debug(
            f"Total lines to translate: {total_lines} "
            f" | Translation segment size: {segment_size}."
        )
        # Process text in segments using segment iteration
        for start_idx, end_idx in num_text.iter_segments(
            segment_size, min_segment_size=MIN_SEGMENT_SIZE
        ):
            translated_content = self.translate_segment(
                num_text=num_text,
                start_line=start_idx,
                end_line=end_idx,
                metadata=metadata,
                source_language=source_language,
                target_language=target_language,
                template_dict=template_dict,
            )

            translated_segments.append(translated_content)

        new_text =  "\n".join(translated_segments).strip()
        
        return text.transform(
            data_str=new_text, 
            language=target_language, 
            )

    def _extract_lines(self, segment: str) -> str:
        if segment.startswith(TRANSCRIPT_SEGMENT_MARKER) and segment.endswith(
            TRANSCRIPT_SEGMENT_MARKER
        ):
            segment = segment[
                len(TRANSCRIPT_SEGMENT_MARKER) : -len(TRANSCRIPT_SEGMENT_MARKER)
            ]
            
        else:
            logger.warning("Translated segment missing transcript_segment tags")

        # clean each line and return full clean segment
        lines = segment.splitlines()
        stripped_lines = [line.strip() for line in lines]
        segment = "\n".join(stripped_lines)
        return segment.strip()

    def _validate_lines(
        self, translated_content: str, start_index: int, end_index: int
    ) -> bool:
        """
        Validate translated segment format, content, and line number sequence.
        Issues warnings for validation issues rather than raising errors.

        Args:
            translated_segment: Translated text to validate
            start_idx: the staring index of the range (inclusive)
            end_line: then ending index of the range (exclusive)

        Returns:
            str: Content with segment tags removed
        """

        # Validate lines

        error_count = 0
        lines = translated_content.splitlines()
        line_numbers = []

        start_line = start_index  # inclusive start
        end_line = end_index - 1  # exclusive end

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if ":" not in line:
                logger.warning(f"Invalid line format: {line}")
                error_count += 1
                continue

            try:
                line_num = int(line[: line.index(":")])
                if line_num < 0:
                    logger.warning(f"Invalid line number: {line}")
                    error_count += 1
                    continue
                line_numbers.append(line_num)
            except ValueError:
                logger.warning(f"Line number parsing failed: {line}")
                error_count += 1
                continue

        # Validate sequence
        if not line_numbers:
            logger.warning("No valid line numbers found")
        else:
            if line_numbers[0] != start_line:
                logger.warning(
                    f"First line number {line_numbers[0]} "
                    f" doesn't match expected {start_line}"
                )
                error_count += 1

            if line_numbers[-1] != end_line:
                logger.warning(
                    f"Last line number {line_numbers[-1]} "
                    f"doesn't match expected {end_line}"
                )
                error_count += 1

            expected = set(range(start_line, end_line + 1))
            if missing := expected - set(line_numbers):
                logger.warning(f"Missing line numbers in sequence: {missing}")
                error_count += len(missing)

        logger.debug(f"Validated {len(lines)} lines from {start_line} to {end_line}\n"
                     f"{error_count} errors encountered.")
        return error_count > 0

def translate_text_by_lines(
    text: TextObject,
    source_language: Optional[str] = None,
    target_language: str = DEFAULT_TARGET_LANGUAGE,
    pattern: Optional[Prompt] = None,
    model: Optional[str] = None,
    style: Optional[str] = None,
    segment_size: Optional[int] = None,
    context_lines: Optional[int] = None,
    review_count: Optional[int] = None,
    template_dict: Optional[Dict] = None,
) -> TextObject:
    
    if source_language is None:
        source_language = text.language

    if pattern is None:
        pattern = get_pattern(DEFAULT_TRANSLATION_PATTERN)
        
    processor = OpenAIProcessor(model)

    translator = LineTranslator(
        processor=processor,
        pattern=pattern,
        style=style or DEFAULT_TRANSLATE_STYLE,
        context_lines=context_lines or DEFAULT_TRANSLATE_CONTEXT_LINES,
        review_count=review_count or DEFAULT_REVIEW_COUNT,
    )

    process_metadata = ProcessMetadata(
            step="translation",
            processor="LineTranslator",
            model=processor.model,
            source_language=source_language,
            target_language=target_language,
            segment_size=segment_size,
            context_lines=translator.context_lines,
            review_count=translator.review_count,
            style=translator.style,
            template_dict=template_dict,
        )

    text = translator.translate_text(
        text,
        source_language=source_language,
        target_language=target_language,
        segment_size=segment_size,
        template_dict=template_dict,
    )
    return text.transform(process_metadata=process_metadata)
