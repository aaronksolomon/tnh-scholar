
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
        ("line1\nline2", 3, None, [(1,3)]), # id: edge_segment_larger_than_text

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
        (-1, None, ValueError), # id: error_negative_segment_size
        (2, 2, ValueError),  # id: error_min_equals_segment_size
        (2, 3, ValueError),  # id: error_min_greater_than_segment_size
    ],
)
def test_iter_segments_errors(segment_size, min_segment_size, expected_error):

    # Arrange
    text = NumberedText("line1\nline2\nline3")

    # Act & Assert
    with pytest.raises(expected_error):
        list(text.iter_segments(segment_size, min_segment_size)) # need to consume iterator for error


def test_iter_segments_empty_text():
    text = NumberedText("")
    with pytest.raises(ValueError):
        list(text.iter_segments(1))
