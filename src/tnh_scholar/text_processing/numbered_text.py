import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Match, NamedTuple, Optional, Set

from pydantic import BaseModel, ConfigDict

from tnh_scholar.utils.file_utils import read_str_from_file, write_str_to_file
from tnh_scholar.utils.math_utils import fraction_to_percent


class NumberedFormat(NamedTuple):
    is_numbered: bool
    separator: Optional[str] = None
    start_num: Optional[int] = None


class SectionValidationError(BaseModel):
    """Error found in section boundaries.

    Error metadata class following tnh-scholar standards:
    - Pydantic v2 BaseModel for validation and serialization
    - Frozen for immutability
    - Used as data structure returned from validation methods

    See: src/tnh_scholar/exceptions.py for exception classes
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    error_type: str  # 'gap', 'overlap', 'out_of_bounds'
    section_index: int  # position in sorted order
    section_input_index: int  # original caller order
    expected_start: int
    actual_start: int
    message: str


class NumberedText:
    """
    Immutable container for text documents with numbered lines.

    Provides utilities for working with line-numbered text including reading,
    writing, accessing lines by number, and iterating over numbered lines.

    Immutability Note:
        NumberedText is designed to be used immutably after construction. While not
        enforced at runtime (for performance reasons as a low-level container),
        instances should not be modified after creation. All operations return new
        data rather than mutating the instance.

    Whitespace and Blank Line Handling (Monaco Editor as standard for compatibility):
        NumberedText follows Monaco Editor's verbatim line and whitespace handling.
        Monaco Editor: https://microsoft.github.io/monaco-editor/typedoc/interfaces/IRange.html

        - Blank lines: Preserved as empty strings in the lines list
        - Whitespace: Leading/trailing whitespace preserved (never stripped)
        - Line count: Blank lines count as lines (e.g., "a\\n\\nb" has 3 lines)
        - Indexing: 1-based line numbers with inclusive end semantics (Monaco IRange)

        Numbered Input Detection:
        When input contains line numbers (e.g., "1: foo\\n2:\\n3: bar"):
        - Pattern validation: Only non-blank lines validated for sequential numbering
        - Number extraction: Removes number prefix (e.g., "2: ") from all lines
        - Blank line handling: After number removal, blank lines become empty strings
        - Example: "1: foo\\n2:\\n3: bar" → lines=[' foo', '', ' bar']

    Attributes:
        lines (List[str]): List of text lines (do not modify after construction)
        start (int): Starting line number (do not modify after construction)
        separator (str): Separator between line number and content (do not modify after construction)

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

    def __init__(self, content: Optional[str] = None, start: int = 1, separator: str = ":") -> None:
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
            raise IndexError("NumberedText: Numbered lines must begin on an integer great or equal to 1.")

        if not content:
            return

        # Analyze the text format
        format_info = get_numbered_format(content)

        if format_info.is_numbered:
            self.start = format_info.start_num  # type: ignore
            self.separator = format_info.separator  # type: ignore

            # Extract content by removing number and separator
            pattern = re.compile(rf"^\d+{re.escape(format_info.separator)}")  # type: ignore
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
        return "\n".join(self._format_line(i, line) for i, line in enumerate(self.lines, self.start))

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

    def get_lines_exclusive(self, start: int, end: int) -> List[str]:
        """Get content of line range [start, end) using 1-based line numbers.

        Args:
            start: Inclusive start line (1-based external indexing).
            end: Exclusive end line (1-based; not included), matching Python slicing semantics.
        """
        return self.lines[self._to_internal_index(start) : self._to_internal_index(end)]

    def get_lines(self, start: int, end: int) -> List[str]:
        """Deprecated: use get_lines_exclusive; end index remains exclusive."""
        return self.get_lines_exclusive(start, end)

    def get_numbered_lines(self, start: int, end: int) -> List[str]:
        """Get numbered lines for [start, end) using 1-based numbering."""
        return [
            self._format_line(line_num, line)
            for line_num, line in enumerate(self.get_lines_exclusive(start, end), start=start)
        ]

    def get_segment(self, start: int, end: int) -> str:
        """Return the segment from start line (inclusive) up to end line (inclusive).

        This aligns with Monaco's inclusive range semantics. Internally we convert
        to Python's exclusive upper bound when slicing.
        """
        if start < self.start:
            raise IndexError(f"Start index {start} is before first line {self.start}")
        if end > self.end:
            raise IndexError(f"End index {end} is past last line {self.end}")
        if start > end:
            raise IndexError(f"Start index {start} must be less than or equal to end index {end}")
        return "\n".join(self.get_lines_exclusive(start, end + 1))

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
        iterator = self.SegmentIterator(len(self), segment_size, self.start, min_segment_size)
        return iter(iterator)

    def get_numbered_segment(self, start: int, end: int) -> str:
        return "\n".join(self.get_numbered_lines(start, end))

    def validate_section_boundaries(self, section_start_lines: List[int]) -> List[SectionValidationError]:
        """Validate section boundaries for gaps, overlaps, and out-of-bounds errors.

        Sections are defined by their start lines; the end of each section is implicit:
        it ends at the line before the next section starts, with the final section ending
        at the last line of the text. Validation enforces:
        - First section starts at self.start
        - No overlaps (next start must be > previous start)
        - No gaps (next start must be exactly previous start + 1)
        - All start lines within [self.start, self.end]
        """
        return self._SectionBoundaryValidator(self, section_start_lines).run()

    class _SectionBoundaryValidator:
        """Stateful validator to keep the main validate_section_boundaries loop simple."""

        def __init__(self, owner: "NumberedText", section_start_lines: List[int]) -> None:
            self.owner = owner
            self.section_start_lines = section_start_lines
            self.errors: List[SectionValidationError] = []
            self.prev_start: Optional[int] = None
            self.first_valid_seen = False

        def run(self) -> List[SectionValidationError]:
            if not self.section_start_lines:
                return self.owner._errors_for_no_sections()

            sorted_with_idx = sorted(enumerate(self.section_start_lines), key=lambda t: t[1])

            for section_index, (input_idx, start_line) in enumerate(sorted_with_idx):
                if self.owner._is_out_of_bounds(start_line):
                    self.errors.append(self.owner._error_out_of_bounds(section_index, input_idx, start_line))
                    continue

                if not self.first_valid_seen:
                    self._handle_first(section_index, input_idx, start_line)
                    continue

                self._handle_body(section_index, input_idx, start_line)

            if not self.first_valid_seen and self.owner.size > 0:
                first_idx, first_start = sorted_with_idx[0]
                self.errors.append(self.owner._error_first_gap(0, first_idx, first_start, no_in_bounds=True))

            return self.errors

        def _handle_first(self, section_index: int, input_idx: int, start_line: int) -> None:
            self.errors.extend(self.owner._errors_for_first_section(section_index, input_idx, start_line))
            self.first_valid_seen = True
            self.prev_start = start_line

        def _handle_body(self, section_index: int, input_idx: int, start_line: int) -> None:
            assert self.prev_start is not None
            if start_line <= self.prev_start:
                self.errors.append(
                    self.owner._error_overlap(section_index, input_idx, self.prev_start, start_line)
                )
            elif start_line > self.prev_start + 1:
                self.errors.append(
                    self.owner._error_gap(section_index, input_idx, self.prev_start, start_line)
                )
            self.prev_start = start_line

    def _is_out_of_bounds(self, start_line: int) -> bool:
        return start_line < self.start or start_line > self.end

    def _errors_for_no_sections(self) -> List[SectionValidationError]:
        if self.size == 0:
            return []
        return [
            SectionValidationError(
                error_type="gap",
                section_index=0,
                section_input_index=-1,
                expected_start=self.start,
                actual_start=self.start - 1,
                message=f"No sections provided; expected first section at line {self.start}",
            )
        ]

    def _errors_for_first_section(
        self, section_index: int, input_idx: int, start_line: int
    ) -> List[SectionValidationError]:
        if start_line == self.start:
            return []
        return [self._error_first_gap(section_index, input_idx, start_line)]

    def _error_first_gap(
        self, section_index: int, input_idx: int, start_line: int, no_in_bounds: bool = False
    ) -> SectionValidationError:
        if no_in_bounds:
            message = f"No in-bounds sections provided; expected first section at line {self.start}"
        else:
            message = (
                f"First section starts at {start_line}, leaving gap at lines {self.start}-{start_line - 1}"
            )
        return SectionValidationError(
            error_type="gap",
            section_index=section_index,
            section_input_index=input_idx,
            expected_start=self.start,
            actual_start=start_line,
            message=message,
        )

    def _error_out_of_bounds(
        self, section_index: int, input_idx: int, start_line: int
    ) -> SectionValidationError:
        return SectionValidationError(
            error_type="out_of_bounds",
            section_index=section_index,
            section_input_index=input_idx,
            expected_start=self.start if start_line < self.start else self.end,
            actual_start=start_line,
            message=(
                f"Section {section_index} start_line {start_line} out of bounds [{self.start}, {self.end}]"
            ),
        )

    def _error_overlap(
        self, section_index: int, input_idx: int, prev_start: int, start_line: int
    ) -> SectionValidationError:
        return SectionValidationError(
            error_type="overlap",
            section_index=section_index,
            section_input_index=input_idx,
            expected_start=prev_start + 1,
            actual_start=start_line,
            message=(f"Section {section_index} has overlap: expected start > {prev_start}, got {start_line}"),
        )

    def _error_gap(
        self, section_index: int, input_idx: int, prev_start: int, start_line: int
    ) -> SectionValidationError:
        return SectionValidationError(
            error_type="gap",
            section_index=section_index,
            section_input_index=input_idx,
            expected_start=prev_start + 1,
            actual_start=start_line,
            message=(f"Section {section_index} has gap: expected start {prev_start + 1}, got {start_line}"),
        )

    def get_coverage_report(self, section_start_lines: List[int]) -> Dict[str, Any]:
        """Return coverage statistics for sections defined by start lines."""
        return self._CoverageReporter(self, section_start_lines).run()

    class _CoverageReporter:
        """Stateful coverage reporter to keep main method concise."""

        def __init__(self, owner: "NumberedText", section_start_lines: List[int]) -> None:
            self.owner = owner
            self.section_start_lines = section_start_lines
            self.covered: Set[int] = set()
            self.overlaps: List[Dict[str, Any]] = []
            self.gaps: List[tuple[int, int]] = []
            self.sorted_starts = sorted(section_start_lines)
            self.prev_valid_start: Optional[int] = None

        def run(self) -> Dict[str, Any]:
            if self.owner.size == 0:
                return self._empty_report()
            if not self.section_start_lines:
                return self._no_sections_report()

            self._seed_initial_gap()
            self._walk_sections()
            self._fill_gaps_from_coverage()
            self._merge_gaps()

            covered_lines = len(self.covered)
            coverage_pct = fraction_to_percent(covered_lines, self.owner.size)

            return {
                "total_lines": self.owner.size,
                "covered_lines": covered_lines,
                "coverage_pct": coverage_pct,
                "gaps": self.gaps,
                "overlaps": self.overlaps,
            }

        def _empty_report(self) -> Dict[str, Any]:
            return {"total_lines": 0, "covered_lines": 0, "coverage_pct": 0.0, "gaps": [], "overlaps": []}

        def _no_sections_report(self) -> Dict[str, Any]:
            return {
                "total_lines": self.owner.size,
                "covered_lines": 0,
                "coverage_pct": 0.0,
                "gaps": [(self.owner.start, self.owner.end)],
                "overlaps": [],
            }

        def _seed_initial_gap(self) -> None:
            first_valid_start = next(
                (s for s in self.sorted_starts if self.owner.start <= s <= self.owner.end),
                None,
            )
            if first_valid_start is None:
                self.gaps.append((self.owner.start, self.owner.end))
            elif first_valid_start > self.owner.start:
                self.gaps.append((self.owner.start, first_valid_start - 1))

        def _walk_sections(self) -> None:
            for i, start in enumerate(self.sorted_starts):
                if start < self.owner.start or start > self.owner.end:
                    continue

                end = self._compute_end(i, start)
                self._maybe_add_gap_between_sections(start)
                self._update_overlaps_and_coverage(i, start, end)
                self.prev_valid_start = start

        def _compute_end(self, index: int, start: int) -> int:
            end = self.sorted_starts[index + 1] - 1 if index < len(self.sorted_starts) - 1 else self.owner.end
            return max(end, start)

        def _maybe_add_gap_between_sections(self, start: int) -> None:
            if self.prev_valid_start is None:
                return
            expected_start = self.prev_valid_start + 1
            if start > expected_start:
                self.gaps.append((expected_start, start - 1))

        def _update_overlaps_and_coverage(self, section_index: int, start: int, end: int) -> None:
            section_lines = set(range(start, end + 1))
            if overlap_lines := self.covered & section_lines:
                self.overlaps.append({"section_index": section_index, "lines": sorted(overlap_lines)})
            self.covered.update(section_lines)

        def _fill_gaps_from_coverage(self) -> None:
            all_lines = set(range(self.owner.start, self.owner.end + 1))
            gap_lines = sorted(all_lines - self.covered)
            if not gap_lines:
                return
            gap_start = gap_lines[0]
            gap_end = gap_lines[0]
            for line in gap_lines[1:]:
                if line == gap_end + 1:
                    gap_end = line
                else:
                    self.gaps.append((gap_start, gap_end))
                    gap_start = gap_end = line
            self.gaps.append((gap_start, gap_end))

        def _merge_gaps(self) -> None:
            if not self.gaps:
                return
            self.gaps = sorted(self.gaps)
            merged: List[tuple[int, int]] = []
            for start, end in self.gaps:
                if not merged or start > merged[-1][1] + 1:
                    merged.append((start, end))
                else:
                    prev_start, prev_end = merged[-1]
                    merged[-1] = (prev_start, max(prev_end, end))
            self.gaps = merged

    def save(self, path: Path, numbered: bool = True) -> None:
        """
        Save document to file.

        Args:
            path: Output file path
            numbered: Whether to save with line numbers (default: True)
        """
        content = str(self) if numbered else "\n".join(self.lines)
        write_str_to_file(path, content)

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
        return [f"{i}{self.separator}{line}" for i, line in enumerate(self.lines, self.start)]

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
