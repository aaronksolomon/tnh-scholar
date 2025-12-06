import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Match, NamedTuple, Optional

from tnh_scholar.utils.file_utils import read_str_from_file, write_str_to_file

# TODO: Revisit whitespace stripping, blank-line handling in numbered inputs, bounds checks
# in get_numbered_lines, and empty-text behavior in iter_segments; keep compatibility until
# a deliberate rewrite is planned.


class NumberedFormat(NamedTuple):
    is_numbered: bool
    separator: Optional[str] = None
    start_num: Optional[int] = None

class NumberedText:
    """
    Represents a text document with numbered lines for easy reference and manipulation.

    Provides utilities for working with line-numbered text including reading,
    writing, accessing lines by number, and iterating over numbered lines.

    Attributes:
        lines (List[str]): List of text lines
        start (int): Starting line number (default: 1)
        separator (str): Separator between line number and content (default: ": ")

    Examples:
        >>> text = "First line\\nSecond line\\n\\nFourth line"
        >>> doc = NumberedText(text)
        >>> print(doc)
        1: First line
        2: Second line
        3:
        4: Fourth line

        >>> print(doc.get_line(2))
        Second line

        >>> for num, line in doc:
        ...     print(f"Line {num}: {len(line)} chars")
    """

    @dataclass
    class LineSegment:
        """
        Represents a segment of lines with start and end indices in 1-based indexing.

        The segment follows Python range conventions where start is inclusive and
        end is exclusive. However, indexing is 1-based to match NumberedText.

        Attributes:
            start: Starting line number (inclusive, 1-based)
            end: Ending line number (exclusive, 1-based)
        """

        start: int
        end: int

        def __iter__(self):
            """Allow unpacking into start, end pairs."""
            yield self.start
            yield self.end

    class SegmentIterator:
        """
        Iterator for generating line segments of specified size.

        Produces segments of lines with start/end indices following 1-based indexing.
        The final segment may be smaller than the specified segment size.

        Attributes:
            total_lines: Total number of lines in text
            segment_size: Number of lines per segment
            start_line: Starting line number (1-based)
            min_segment_size: Minimum size for the final segment
        """

        def __init__(
            self,
            total_lines: int,
            segment_size: int,
            start_line: int = 1,
            min_segment_size: Optional[int] = None,
        ):
            """
            Initialize the segment iterator.

            Args:
                total_lines: Total number of lines to iterate over
                segment_size: Desired size of each segment
                start_line: First line number (default: 1)
                min_segment_size: Minimum size for final segment (default: None)
                    If specified, the last segment will be merged with the previous one
                    if it would be smaller than this size.

            Raises:
                ValueError: If segment_size < 1 or total_lines < 1
                ValueError: If start_line < 1 (must use 1-based indexing)
                ValueError: If min_segment_size >= segment_size
            """
            if segment_size < 1:
                raise ValueError("Segment size must be at least 1")
            if total_lines < 1:
                raise ValueError("Total lines must be at least 1")
            if start_line < 1:
                raise ValueError("Start line must be at least 1 (1-based indexing)")
            if min_segment_size is not None and min_segment_size >= segment_size:
                raise ValueError("Minimum segment size must be less than segment size")

            self.total_lines = total_lines
            self.segment_size = segment_size
            self.start_line = start_line
            self.min_segment_size = min_segment_size

            # Calculate number of segments
            remaining_lines = total_lines - start_line + 1
            self.num_segments = (remaining_lines + segment_size - 1) // segment_size

        def __iter__(self) -> Iterator["NumberedText.LineSegment"]:
            """
            Iterate over line segments.

            Yields:
                LineSegment containing start (inclusive) and end (exclusive) indices
            """
            current = self.start_line

            for i in range(self.num_segments):
                is_last_segment = i == self.num_segments - 1
                segment_end = min(current + self.segment_size, self.total_lines + 1)

                # Handle minimum segment size for last segment
                if (
                    is_last_segment
                    and self.min_segment_size is not None
                    and segment_end - current < self.min_segment_size
                    and i > 0
                ):
                    # Merge with previous segment by not yielding
                    break

                yield NumberedText.LineSegment(current, segment_end)
                current = segment_end

    def __init__(
        self, content: Optional[str] = None, start: int = 1, separator: str = ":"
    ) -> None:
        """
        Initialize a numbered text document, 
        detecting and preserving existing numbering.

        Valid numbered text must have:
        - Sequential line numbers
        - Consistent separator character(s)
        - Every non-empty line must follow the numbering pattern

        Args:
            content: Initial text content, if any
            start: Starting line number (used only if content isn't already numbered)
            separator: Separator between line numbers and content (only if content isn't numbered)

        Examples:
            >>> # Custom separators
            >>> doc = NumberedText("1→First line\\n2→Second line")
            >>> doc.separator == "→"
            True

            >>> # Preserves starting number
            >>> doc = NumberedText("5#First\\n6#Second")
            >>> doc.start == 5
            True

            >>> # Regular numbered list isn't treated as line numbers
            >>> doc = NumberedText("1. First item\\n2. Second item")
            >>> doc.numbered_lines
            ['1: 1. First item', '2: 2. Second item']
        """

        self.lines: List[str] = []  # Declare lines here
        self.start: int = start  # Declare start with its type
        self.separator: str = separator  # and separator

        if not isinstance(content, str):
            raise ValueError("NumberedText requires string input.")

        if start < 1:  # enforce 1 based indexing.
            raise IndexError(
                "NumberedText: Numbered lines must begin on "
                "an integer great or equal to 1."
            )

        if not content:
            return

        # Analyze the text format
        is_numbered, detected_sep, start_num = get_numbered_format(content)

        format_info = get_numbered_format(content)

        if format_info.is_numbered:
            self.start = format_info.start_num  # type: ignore
            self.separator = format_info.separator  # type: ignore

            # Extract content by removing number and separator
            pattern = re.compile(rf"^\d+{re.escape(detected_sep)}") # type: ignore
            self.lines = []

            for line in content.splitlines():
                if line.strip():
                    self.lines.append(pattern.sub("", line))
                else:
                    self.lines.append(line)
        else:
            self.lines = content.splitlines()
            self.start = start
            self.separator = separator

    @classmethod
    def from_file(cls, path: Path, **kwargs) -> "NumberedText":
        """Create a NumberedText instance from a file."""
        return cls(read_str_from_file(Path(path)), **kwargs)

    def _format_line(self, line_num: int, line: str) -> str:
        return f"{line_num}{self.separator}{line}"

    def _to_internal_index(self, idx: int) -> int:
        """return the index into the lines object in Python 0-based indexing."""
        if idx > 0:
            return idx - self.start
        elif idx < 0:  # allow negative indexing to index from end
            if abs(idx) > self.size:
                raise IndexError(f"NumberedText: negative index out of range: {idx}")
            return self.end + idx  # convert to logical positive location for reference.
        else:
            raise IndexError("NumberedText: Index cannot be zero in 1-based indexing.")

    def __str__(self) -> str:
        """Return the numbered text representation."""
        return "\n".join(
            self._format_line(i, line) for i, line in enumerate(self.lines, self.start)
        )

    def __len__(self) -> int:
        """Return the number of lines."""
        return len(self.lines)

    def __iter__(self) -> Iterator[tuple[int, str]]:
        """Iterate over (line_number, line_content) pairs."""
        return iter((i, line) for i, line in enumerate(self.lines, self.start))

    def __getitem__(self, index: int) -> str:
        """Get line content by line number (1-based indexing)."""
        return self.lines[self._to_internal_index(index)]

    def get_line(self, line_num: int) -> str:
        """Get content of specified line number."""
        return self[line_num]

    def _to_line_index(self, internal_index: int) -> int:
        return self.start + self._to_internal_index(internal_index)

    def get_numbered_line(self, line_num: int) -> str:
        """Get specified line with line number."""
        idx = self._to_line_index(line_num)
        return self._format_line(idx, self[idx])

    def get_lines(self, start: int, end: int) -> List[str]:
        """Get content of line range, not inclusive of end line."""
        return self.lines[self._to_internal_index(start) : self._to_internal_index(end)]

    def get_numbered_lines(self, start: int, end: int) -> List[str]:
        return [
            self._format_line(i + self._to_internal_index(start) + 1, line)
            for i, line in enumerate(self.get_lines(start, end))
        ]
    def get_segment(self, start: int, end: int) -> str:
        """return the segment from start line (inclusive) up to end line (exclusive)"""
        if start < self.start:
            raise IndexError(f"Start index {start} is before first line {self.start}")
        if end > len(self) + 1:
            raise IndexError(f"End index {end} is past last line {len(self)}")
        if start >= end:
            raise IndexError(f"Start index {start} must be less than end index {end}")
        return "\n".join(self.get_lines(start, end))

    def iter_segments(
        self, segment_size: int, min_segment_size: Optional[int] = None
    ) -> Iterator[LineSegment]:
        """
        Iterate over segments of the text with specified size.

        Args:
            segment_size: Number of lines per segment
            min_segment_size: Optional minimum size for final segment.
                If specified, last segment will be merged with previous one
                if it would be smaller than this size.

        Yields:
            LineSegment objects containing start and end line numbers

        Example:
            >>> text = NumberedText("line1\\nline2\\nline3\\nline4\\nline5")
            >>> for segment in text.iter_segments(2):
            ...     print(f"Lines {segment.start}-{segment.end}")
            Lines 1-3
            Lines 3-5
            Lines 5-6
        """
        iterator = self.SegmentIterator(
            len(self), segment_size, self.start, min_segment_size
        )
        return iter(iterator)

    def get_numbered_segment(self, start: int, end: int) -> str:
        return "\n".join(self.get_numbered_lines(start, end))

    def save(self, path: Path, numbered: bool = True) -> None:
        """
        Save document to file.

        Args:
            path: Output file path
            numbered: Whether to save with line numbers (default: True)
        """
        content = str(self) if numbered else "\n".join(self.lines)
        write_str_to_file(path, content)

    def append(self, text: str) -> None:
        """Append text, splitting into lines if needed."""
        self.lines.extend(text.splitlines())

    def insert(self, line_num: int, text: str) -> None:
        """Insert text at specified line number. Assumes text is not empty."""
        new_lines = text.splitlines()
        internal_idx = self._to_internal_index(line_num)
        self.lines[internal_idx:internal_idx] = new_lines

    def reset_numbering(self):
        self.start = 1
        
    def remove_whitespace(self) -> None:
        """Remove leading and trailing whitespace from all lines."""
        self.lines = [line.strip() for line in self.lines]
        
    @property
    def content(self) -> str:
        """Get original text without line numbers."""
        return "\n".join(self.lines)
    
    @property
    def numbered_content(self) -> str:
        """Get text with line numbers as a string. Equivalent to str(self)"""
        return str(self)

    @property
    def size(self) -> int:
        """Get the number of lines."""
        return len(self.lines)

    @property
    def numbered_lines(self) -> List[str]:
        """
        Get list of lines with line numbers included.

        Returns:
            List[str]: Lines with numbers and separator prefixed

        Examples:
            >>> doc = NumberedText("First line\\nSecond line")
            >>> doc.numbered_lines
            ['1: First line', '2: Second line']

        Note:
            - Unlike str(self), this returns a list rather than joined string
            - Maintains consistent formatting with separator
            - Useful for processing or displaying individual numbered lines
        """
        return [
            f"{i}{self.separator}{line}"
            for i, line in enumerate(self.lines, self.start)
        ]

    @property
    def end(self) -> int:
        return self.start + len(self.lines) - 1


def get_numbered_format(text: str) -> NumberedFormat:
    """
    Analyze text to determine if it follows a consistent line numbering format.

    Valid formats have:
    - Sequential numbers starting from some value
    - Consistent separator character(s)
    - Every line must follow the format

    Args:
        text: Text to analyze

    Returns:
        Tuple of (is_numbered, separator, start_number)

    Examples:
        >>> _analyze_numbered_format("1→First\\n2→Second")
        (True, "→", 1)
        >>> _analyze_numbered_format("1. First")  # Numbered list format
        (False, None, None)
        >>> _analyze_numbered_format("5#Line\\n6#Other")
        (True, "#", 5)
    """
    if not text.strip():
        return NumberedFormat(False)

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return NumberedFormat(False)

    # Try to detect pattern from first line
    SEPARATOR_PATTERN = r"[^\w\s.]"  # not (word char or whitespace or period)
    first_match = re.match(rf"^(\d+)({SEPARATOR_PATTERN})(.*?)$", lines[0])

    if not first_match:
        return NumberedFormat(False)
    try:
        return _check_line_structure(first_match, lines)
    except (ValueError, AttributeError):
        return NumberedFormat(False)

def _check_line_structure(first_match: Match[str], lines: List[str]) -> NumberedFormat:
    start_num = int(first_match.group(1))  # type: ignore
    separator = str(first_match.group(2))  # type: ignore

    # Don't treat numbered list format as line numbers
    if separator == ".":
        return NumberedFormat(False)

    # Verify all lines follow the pattern with sequential numbers
    for i, line in enumerate(lines):
        expected_num = start_num + i
        expected_prefix = f"{expected_num}{separator}"

        if not line.startswith(expected_prefix):
            return NumberedFormat(False)

    return NumberedFormat(True, separator, start_num)
