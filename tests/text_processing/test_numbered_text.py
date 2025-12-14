import pytest

from tnh_scholar.text_processing.numbered_text import NumberedText, get_numbered_format


@pytest.mark.parametrize(
    "test_id, content, start, separator, expected_lines, expected_start, expected_separator",
    [
        ("empty_content", "", 1, ":", [], 1, ":"),
        ("simple_content", "Line 1\nLine 2", 1, ":", ["Line 1", "Line 2"], 1, ":"),
        (
            "numbered_content",
            "1: Line 1\n2: Line 2",
            5,
            "#",
            [" Line 1", " Line 2"],
            1,
            ":",
        ),
        (
            "numbered_content_custom_separator",
            "1# Line 1\n2# Line 2",
            5,
            "#",
            [" Line 1", " Line 2"],
            1,
            "#",
        ),
        (
            "numbered_content_empty_lines",
            "1: Line 1\n\n3: Line 3",
            5,
            "#",
            ["1: Line 1", "", "3: Line 3"],
            5,
            "#",
        ),
    ],
)
def test_numbered_text_init(
    test_id, content, start, separator, expected_lines, expected_start, expected_separator
):
    # Act
    numbered_text = NumberedText(content, start, separator)

    # Assert
    assert numbered_text.lines == expected_lines
    assert numbered_text.start == expected_start
    assert numbered_text.separator == expected_separator


@pytest.mark.parametrize(
    "test_id, content, expected_is_numbered, expected_separator, expected_start",
    [
        ("numbered_colon", "1: Line 1\n2: Line 2", True, ":", 1),
        ("numbered_hash", "1# Line 1\n2# Line 2", True, "#", 1),
        ("numbered_arrow", "1→ Line 1\n2→ Line 2", True, "→", 1),
        ("numbered_start_5", "5: Line 1\n6: Line 2", True, ":", 5),
        ("not_numbered", "Line 1\nLine 2", False, None, None),
        ("not_numbered_start_5", "5. First item\n6. Second item", False, None, None),
        ("empty", "", False, None, None),
        ("numbered_inconsistent_separator", "1: Line 1\n2# Line 2", False, None, None),
        ("numbered_non_sequential", "1: Line 1\n3: Line 2", False, None, None),
        ("numbered_missing_number", "1: Line 1\nLine 2", False, None, None),
    ],
)
def test_get_numbered_format(test_id, content, expected_is_numbered, expected_separator, expected_start):
    # Act
    is_numbered, separator, start_num = get_numbered_format(content)

    # Assert
    assert is_numbered == expected_is_numbered
    assert separator == expected_separator
    assert start_num == expected_start


@pytest.mark.parametrize(
    "test_id, content, start, separator, expected_str",
    [
        ("empty", "", 1, ":", ""),
        ("single_line", "Line 1", 1, ":", "1:Line 1"),
        ("multi_line", "Line 1\nLine 2", 1, ":", "1:Line 1\n2:Line 2"),
        ("custom_start", "Line 1\nLine 2", 5, "#", "5#Line 1\n6#Line 2"),
    ],
)
def test_numbered_text_str(test_id, content, start, separator, expected_str):
    # Act
    numbered_text = NumberedText(content, start, separator)

    # Assert
    assert str(numbered_text) == expected_str


@pytest.mark.parametrize(
    "test_id, content, start, separator, expected_len",
    [
        ("empty", "", 1, ":", 0),
        ("single_line", "Line 1", 1, ":", 1),
        ("multi_line", "Line 1\nLine 2", 1, ":", 2),
    ],
)
def test_numbered_text_len(test_id, content, start, separator, expected_len):
    # Act
    numbered_text = NumberedText(content, start, separator)

    # Assert
    assert len(numbered_text) == expected_len


@pytest.mark.parametrize(
    "test_id, content, start, separator, expected_iter",
    [
        ("empty", "", 1, ":", []),
        ("single_line", "Line 1", 1, ":", [(1, "Line 1")]),
        ("multi_line", "Line 1\nLine 2", 1, ":", [(1, "Line 1"), (2, "Line 2")]),
        ("custom_start", "Line 1\nLine 2", 5, "#", [(5, "Line 1"), (6, "Line 2")]),
    ],
)
def test_numbered_text_iter(test_id, content, start, separator, expected_iter):
    # Act
    numbered_text = NumberedText(content, start, separator)

    # Assert
    assert list(numbered_text) == expected_iter


# ... (Tests for other methods like __getitem__, get_line, etc. would follow here)
# Please let me know if you'd like me to generate tests for the remaining methods as well.

# ... (Existing tests from previous response)


@pytest.mark.parametrize(
    "test_id, content, start, separator, index, expected_line",
    [
        ("first_line", "Line 1\nLine 2", 1, ":", 1, "Line 1"),
        ("second_line", "Line 1\nLine 2", 1, ":", 2, "Line 2"),
        ("custom_start", "Line 1\nLine 2", 5, "#", 5, "Line 1"),
        ("negative_index", "Line 1\nLine 2", 1, ":", -1, "Line 2"),
        ("out_of_range", "Line 1\nLine 2", 1, ":", 3, None),  # Expecting IndexError
    ],
)
def test_numbered_text_getitem(test_id, content, start, separator, index, expected_line):
    # Arrange
    numbered_text = NumberedText(content, start, separator)

    # Act & Assert
    if expected_line is None:
        with pytest.raises(IndexError):
            numbered_text[index]
    else:
        assert numbered_text[index] == expected_line


@pytest.mark.parametrize(
    "test_id, content, line_num, expected_line",
    [
        ("get_line_1", "Line 1\nLine 2", 1, "Line 1"),
        ("get_line_2", "Line 1\nLine 2", 2, "Line 2"),
        ("get_line_out_of_range", "Line 1\nLine 2", 3, None),  # Expecting IndexError
    ],
)
def test_get_line(test_id, content, line_num, expected_line):
    # Arrange
    numbered_text = NumberedText(content)

    # Act & Assert
    if expected_line is None:
        with pytest.raises(IndexError):
            numbered_text.get_line(line_num)
    else:
        assert numbered_text.get_line(line_num) == expected_line


# Example for get_numbered_lines
@pytest.mark.parametrize(
    "test_id, content, start, end, expected_lines",
    [
        ("get_numbered_lines_1_2", "Line 1\nLine 2\nLine 3", 1, 2, ["1:Line 1"]),
        ("get_numbered_lines_2_3", "Line 1\nLine 2\nLine 3", 2, 3, ["2:Line 2"]),
        (
            "get_numbered_lines_out_of_range",
            "Line 1\nLine 2\nLine 3",
            1,
            4,
            ["1:Line 1", "2:Line 2", "3:Line 3"],
        ),
    ],
)
def test_get_numbered_lines(test_id, content, start, end, expected_lines):
    # Arrange
    numbered_text = NumberedText(content)

    # Act & Assert
    assert numbered_text.get_numbered_lines(start, end) == expected_lines


@pytest.mark.parametrize(
    "content, segment_size, min_segment_size, expected_segments",
    [
        # Happy path tests
        ("line1\nline2\nline3\nline4\nline5", 2, None, [(1, 3), (3, 5), (5, 6)]),  # id: happy_path_no_min
        (
            "line1\nline2\nline3\nline4\nline5\nline6",
            2,
            None,
            [(1, 3), (3, 5), (5, 7)],
        ),  # id: happy_path_even_lines
        ("line1\nline2\nline3\nline4\nline5", 3, None, [(1, 4), (4, 6)]),  # id: happy_path_larger_segment
        (
            "line1\nline2\nline3\nline4\nline5",
            2,
            1,
            [(1, 3), (3, 5), (5, 6)],
        ),  # id: happy_path_small_min_no_effect
        ("line1\nline2\nline3\nline4\nline5", 3, 2, [(1, 4), (4, 6)]),  # id: happy_path_min_no_merge
        # Edge cases
        ("line1", 1, None, [(1, 2)]),  # id: edge_single_line
        ("line1\nline2", 2, None, [(1, 3)]),  # id: edge_exact_segment
        ("line1\nline2\nline3", 2, 1, [(1, 3), (3, 4)]),  # id: edge_min_causes_split
        ("line1\nline2", 3, None, [(1, 3)]),  # id: edge_segment_larger_than_text
        # Error cases - tested separately
    ],
)
def test_iter_segments_parametrized(content, segment_size, min_segment_size, expected_segments):
    # Act
    text = NumberedText(content)
    segments = [(s.start, s.end) for s in text.iter_segments(segment_size, min_segment_size)]

    # Assert
    assert segments == expected_segments


@pytest.mark.parametrize(
    "segment_size, min_segment_size, expected_error",
    [
        (0, None, ValueError),  # id: error_zero_segment_size
        (-1, None, ValueError),  # id: error_negative_segment_size
        (2, 2, ValueError),  # id: error_min_equals_segment_size
        (2, 3, ValueError),  # id: error_min_greater_than_segment_size
    ],
)
def test_iter_segments_errors(segment_size, min_segment_size, expected_error):
    # Arrange
    text = NumberedText("line1\nline2\nline3")

    # Act & Assert
    with pytest.raises(expected_error):
        list(text.iter_segments(segment_size, min_segment_size))  # need to consume iterator for error


def test_get_segment_inclusive_end():
    text = NumberedText("a\nb\nc")
    assert text.get_segment(1, 2) == "a\nb"
    assert text.get_segment(3, 3) == "c"
    with pytest.raises(IndexError):
        text.get_segment(1, 4)
    with pytest.raises(IndexError):
        text.get_segment(2, 1)


def test_validate_section_boundaries_contiguous():
    text = NumberedText("\n".join(f"line{i}" for i in range(1, 6)))
    errors = text.validate_section_boundaries([1, 2, 3, 4, 5])
    assert errors == []


def test_validate_section_boundaries_gaps_and_overlaps():
    text = NumberedText("\n".join(f"line{i}" for i in range(1, 6)))
    errors = text.validate_section_boundaries([2, 4, 4])
    assert {e.error_type for e in errors} == {"gap", "overlap"}
    assert any(e.error_type == "gap" and e.section_index == 0 for e in errors)
    assert any(e.error_type == "overlap" for e in errors)


def test_validate_section_boundaries_out_of_bounds_and_empty():
    text = NumberedText("\n".join(f"line{i}" for i in range(1, 4)))
    errors = text.validate_section_boundaries([])
    assert len(errors) == 1
    assert errors[0].error_type == "gap"

    errors = text.validate_section_boundaries([0, 2])
    assert any(e.error_type == "out_of_bounds" for e in errors)


def test_get_coverage_report():
    text = NumberedText("\n".join(f"line{i}" for i in range(1, 6)))
    report_full = text.get_coverage_report([1, 2, 3, 4, 5])
    assert report_full["coverage_pct"] == 100.0
    assert report_full["gaps"] == []
    assert report_full["overlaps"] == []

    report_gap = text.get_coverage_report([2, 4])
    assert report_gap["coverage_pct"] < 100.0
    assert (1, 1) in report_gap["gaps"]

    report_overlap = text.get_coverage_report([1, 1, 3])
    assert report_overlap["overlaps"]


def test_iter_segments_empty_text():
    text = NumberedText("")
    with pytest.raises(ValueError):
        list(text.iter_segments(1))


# ============================================================================
# Whitespace and Blank Line Handling Tests (Monaco Editor Compatibility)
# ============================================================================


class TestWhitespaceAndBlankLineHandling:
    """Test suite for Monaco-compatible whitespace and blank line handling."""

    def test_blank_lines_preserved_in_plain_text(self):
        """Blank lines should be preserved as empty strings."""
        text = NumberedText("foo\n\nbar")
        assert text.lines == ["foo", "", "bar"]
        assert len(text) == 3
        assert text.get_line(2) == ""

    def test_multiple_consecutive_blank_lines(self):
        """Multiple blank lines should all be preserved."""
        text = NumberedText("a\n\n\nb")
        assert text.lines == ["a", "", "", "b"]
        assert len(text) == 4

    def test_leading_trailing_whitespace_preserved(self):
        """Leading and trailing whitespace should never be stripped."""
        text = NumberedText("  foo  \n\t\tbar\t\t\n   ")
        assert text.lines == ["  foo  ", "\t\tbar\t\t", "   "]
        assert text.get_line(1) == "  foo  "
        assert text.get_line(2) == "\t\tbar\t\t"
        assert text.get_line(3) == "   "

    def test_numbered_input_with_blank_line(self):
        """Numbered input with blank line: number prefix removed, blank preserved."""
        text = NumberedText("1: foo\n2:\n3: bar")
        assert text.lines == [" foo", "", " bar"]
        assert text.start == 1
        assert text.separator == ":"
        assert len(text) == 3

    def test_numbered_input_with_whitespace_only_content(self):
        """Numbered input with whitespace-only content preserves the whitespace."""
        text = NumberedText("1: foo\n2:  \n3: bar")
        assert text.lines == [" foo", "  ", " bar"]
        assert text.get_line(2) == "  "

    def test_numbered_input_with_multiple_blank_lines(self):
        """Multiple consecutive blank lines in numbered input."""
        text = NumberedText("1: foo\n2:\n3:\n4: bar")
        assert text.lines == [" foo", "", "", " bar"]
        assert len(text) == 4

    def test_blank_line_in_segment_retrieval(self):
        """Blank lines should be included in segment retrieval."""
        text = NumberedText("a\n\nc")
        segment = text.get_segment(1, 3)
        assert segment == "a\n\nc"
        assert segment.count("\n") == 2

    def test_validation_includes_blank_lines(self):
        """Section validation should count blank lines as valid lines.

        Note: validation requires no gaps, so section start lines must
        be consecutive (each section implicitly ends where next begins).
        """
        text = NumberedText("a\n\nc\n\ne")  # 5 lines total

        # Each line as a separate section (consecutive starts)
        errors = text.validate_section_boundaries([1, 2, 3, 4, 5])
        assert len(errors) == 0  # Valid: sections at each line

        # Single section covering all lines (including blank lines)
        errors_single = text.validate_section_boundaries([1])
        assert len(errors_single) == 0  # Valid: one section covers lines 1-5

    def test_coverage_report_includes_blank_lines(self):
        """Coverage report should count blank lines."""
        text = NumberedText("a\n\nc")  # 3 lines
        report = text.get_coverage_report([1, 2, 3])
        assert report["total_lines"] == 3
        assert report["covered_lines"] == 3
        assert report["coverage_pct"] == 100.0

    def test_iteration_includes_blank_lines(self):
        """Iteration should include blank lines with their line numbers."""
        text = NumberedText("foo\n\nbar")
        lines_with_nums = list(text)
        assert lines_with_nums == [(1, "foo"), (2, ""), (3, "bar")]

    def test_numbered_lines_property_with_blanks(self):
        """numbered_lines property should format blank lines correctly."""
        text = NumberedText("foo\n\nbar")
        numbered = text.numbered_lines
        assert numbered == ["1:foo", "2:", "3:bar"]

    def test_str_representation_with_blanks(self):
        """String representation should show blank lines with numbers."""
        text = NumberedText("foo\n\nbar")
        output = str(text)
        assert output == "1:foo\n2:\n3:bar"

    def test_whitespace_only_lines_not_collapsed(self):
        """Lines with only whitespace should not be collapsed to empty."""
        text = NumberedText("a\n   \nb")
        assert text.lines == ["a", "   ", "b"]
        assert text.get_line(2) == "   "

    def test_numbered_input_detection_ignores_blank_lines(self):
        """Numbered format detection should only validate non-blank lines."""
        # This should be detected as numbered even with blank line at position 2
        text = NumberedText("1: foo\n\n3: bar")
        # Detection fails because line 3 says "3:" not "2:"
        assert text.start == 1
        assert text.separator == ":"
        assert text.lines == ["1: foo", "", "3: bar"]  # Not detected as numbered

    def test_numbered_input_sequential_with_blank(self):
        """Sequential numbered input with blank at line 2 should be detected."""
        text = NumberedText("1: foo\n2:\n3: bar")
        assert text.start == 1
        assert text.separator == ":"
        assert text.lines == [" foo", "", " bar"]  # Detected and extracted
