import pytest
from typing import Iterator, List, Optional, Tuple
import re
from tnh_scholar.text_processing.numbered_text import NumberedText

class TestNumberedText:
    @pytest.mark.parametrize(
        "text, expected_lines, expected_start, expected_separator",
        [
            ("First line\nSecond line\n\nFourth line", ["First line", "Second line", "", "Fourth line"], 1, ": "),  # Basic test
            ("", [], 1, ": "),  # Empty text
            ("Single line", ["Single line"], 1, ": "),  # Single line
            ("Line 1\nLine 2\nLine 3", ["Line 1", "Line 2", "Line 3"], 1, ": "),  # Multiple lines
            ("Line with spaces\n  Indented line\n\tTab indented", ["Line with spaces", "  Indented line", "\tTab indented"], 1, ": "),  # Whitespace handling
        ],
        ids=["basic", "empty", "single_line", "multiple_lines", "whitespace"]
    )
    def test_init_happy_path(self, text, expected_lines, expected_start, expected_separator):
        # Act
        numbered_text = NumberedText(text, start=expected_start, separator=expected_separator)

        # Assert
        assert numbered_text.lines == expected_lines
        assert numbered_text.start == expected_start
        assert numbered_text.separator == expected_separator

    @pytest.mark.parametrize(
        "start, separator",
        [
            (0, ": "),  # Start at 0
            (-1, ": "), # Negative start
            (10, " - "),  # Different separator
            (1, "->"), # Another separator
        ],
        ids=["start_zero", "negative_start", "different_separator", "another_separator"]

    )
    def test_init_edge_cases(self, start, separator):
        text = "First line\nSecond line"

        # Act
        numbered_text = NumberedText(text, start=start, separator=separator)

        # Assert
        assert numbered_text.start == start
        assert numbered_text.separator == separator


    def test_get_line_happy_path(self):
        text = "First line\nSecond line\nThird line"
        numbered_text = NumberedText(text)

        # Act
        line = numbered_text.get_line(2)

        # Assert
        assert line == "Second line"

    @pytest.mark.parametrize(
        "line_number, expected_line",
        [
            (1, "First line"),  # First line
            (3, "Third line"),  # Last line
        ],
        ids=["first_line", "last_line"]
    )
    def test_get_line_edge_cases(self, line_number, expected_line):
        text = "First line\nSecond line\nThird line"
        numbered_text = NumberedText(text)

        # Act
        line = numbered_text.get_line(line_number)

        # Assert
        assert line == expected_line


    @pytest.mark.parametrize(
        "line_number",
        [
            (0),  # Line number too low
            (4),  # Line number too high
            (-1), # Negative line number
        ],
        ids=["too_low", "too_high", "negative"]
    )
    def test_get_line_error_cases(self, line_number):
        text = "First line\nSecond line\nThird line"
        numbered_text = NumberedText(text)

        # Act & Assert
        with pytest.raises(IndexError):
            numbered_text.get_line(line_number)

    def test_iter_happy_path(self):
        text = "First line\nSecond line\nThird line"
        numbered_text = NumberedText(text)
        expected_output = [(1, "First line"), (2, "Second line"), (3, "Third line")]

        # Act
        actual_output = list(numbered_text)

        # Assert
        assert actual_output == expected_output

    def test_iter_empty_text(self):
        text = ""
        numbered_text = NumberedText(text)
        expected_output = []

        # Act
        actual_output = list(numbered_text)

        # Assert
        assert actual_output == expected_output

    def test_str_happy_path(self):
        text = "First line\nSecond line\nThird line"
        numbered_text = NumberedText(text, start=1, separator=": ")
        expected_output = "1: First line\n2: Second line\n3: Third line"

        # Act
        actual_output = str(numbered_text)

        # Assert
        assert actual_output == expected_output

    @pytest.mark.parametrize(
        "start, separator, expected_output",
        [
            (0, ": ", "0: First line\n1: Second line\n2: Third line"),  # Start at 0
            (1, "->", "1->First line\n2->Second line\n3->Third line"),  # Different separator
            (10, ". ", "10. First line\n11. Second line\n12. Third line"), # Start at 10 and different separator
        ],
        ids=["start_zero", "different_separator", "start_10_different_separator"]
    )
    def test_str_edge_cases(self, start, separator, expected_output):
        text = "First line\nSecond line\nThird line"
        numbered_text = NumberedText(text, start=start, separator=separator)

        # Act
        actual_output = str(numbered_text)

        # Assert
        assert actual_output == expected_output


