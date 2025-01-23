import re

#### NOTE THIS MODULE DEPRECATED available for reference and development purposes ####

class FormattingError(Exception):
    """
    Custom exception raised for formatting-related errors.
    """

    def __init__(self, message="An error occurred due to invalid formatting."):
        super().__init__(message)


# functions to bracket and unbracket text with line numbers

def bracket_lines(text: str, number: bool = False) -> str:
    """
    Encloses each line of the input text with angle brackets.
    If number is True, adds a line number followed by a colon `:` and then the line.

    Args:
        text (str): The input string containing lines separated by '\n'.
        number (bool): Whether to prepend line numbers to each line.

    Returns:
        str: A string where each line is enclosed in angle brackets.

    Examples:
        >>> bracket_lines("This is a string with\n   two lines.")
        '<This is a string with>\n<   two lines.>'

        >>> bracket_lines("This is a string with\n   two lines.", number=True)
        '<1:This is a string with>\n<2:   two lines.>'
    """
    return "\n".join(
        f"<{f'{i+1}:{line}' if number else line}>"
        for i, line in enumerate(text.split("\n"))
    )


def number_lines(text: str, start: int = 1, separator: str = ": ") -> str:
    """
    Numbers each line of text with a readable format, including empty lines.

    Args:
        text (str): Input text to be numbered. Can be multi-line.
        start (int, optional): Starting line number. Defaults to 1.
        separator (str, optional): Separator between line number and content.
            Defaults to ": ".

    Returns:
        str: Numbered text where each line starts with "{number}: ".

    Examples:
        >>> text = "First line\\nSecond line\\n\\nFourth line"
        >>> print(number_lines(text))
        1: First line
        2: Second line
        3:
        4: Fourth line

        >>> print(number_lines(text, start=5, separator=" | "))
        5 | First line
        6 | Second line
        7 |
        8 | Fourth line

    Notes:
        - All lines are numbered, including empty lines, to maintain text structure
        - Line numbers are aligned through natural string formatting
        - Customizable separator allows for different formatting needs
        - Can start from any line number for flexibility in text processing
    """
    lines = text.splitlines()
    return "\n".join(f"{i}{separator}{line}" for i, line in enumerate(lines, start))


def bracket_all_lines(pages):
    return [bracket_lines(page) for page in pages]


def unbracket_lines(text: str, number: bool = False) -> str:
    """
    Removes angle brackets (< >) from encapsulated lines and optionally removes line numbers.

    Args:
        text (str): The input string with encapsulated lines.
        number (bool): If True, removes line numbers in the format 'digit:'.
                       Raises a ValueError if `number=True` and a line does not start with a digit followed by a colon.

    Returns:
        str: A newline-separated string with the encapsulation removed, and line numbers stripped if specified.

    Examples:
        >>> unbracket_lines("<1:Line 1>\n<2:Line 2>", number=True)
        'Line 1\nLine 2'

        >>> unbracket_lines("<Line 1>\n<Line 2>")
        'Line 1\nLine 2'

        >>> unbracket_lines("<1Line 1>", number=True)
        ValueError: Line does not start with a valid number: '1Line 1'
    """
    unbracketed_lines = []

    for line in text.splitlines():
        match = (
            re.match(r"<(\d+):(.*?)>", line) if number else re.match(r"<(.*?)>", line)
        )
        if match:
            content = match[2].strip() if number else match[1].strip()
            unbracketed_lines.append(content)
        elif number:
            raise FormattingError(f"Line does not start with a valid number: '{line}'")
        else:
            raise FormattingError(f"Line does not follow the expected format: '{line}'")

    return "\n".join(unbracketed_lines)


def unbracket_all_lines(pages):
    result = []
    for page in pages:
        if page == "blank page":
            result.append(page)
        else:
            result.append(unbracket_lines(page))
    return result


def lines_from_bracketed_text(
    text: str, start: int, end: int, keep_brackets=False
) -> list[str]:
    """
    Extracts lines from bracketed text between the start and end indices, inclusive.
    Handles both numbered and non-numbered cases.

    Args:
        text (str): The input bracketed text containing lines like <...>.
        start (int): The starting line number (1-based).
        end (int): The ending line number (1-based).

    Returns:
        list[str]: The lines from start to end inclusive, with angle brackets removed.

    Raises:
        FormattingError: If the text contains improperly formatted lines (missing angle brackets).
        ValueError: If start or end indices are invalid or out of bounds.

    Examples:
        >>> text = "<1:Line 1>\n<2:Line 2>\n<3:Line 3>"
        >>> lines_from_bracketed_text(text, 1, 2)
        ['Line 1', 'Line 2']

        >>> text = "<Line 1>\n<Line 2>\n<Line 3>"
        >>> lines_from_bracketed_text(text, 2, 3)
        ['Line 2', 'Line 3']
    """
    # Split the text into lines
    lines = text.splitlines()

    # Validate indices
    if start < 1 or end < 1 or start > end or end > len(lines):
        raise ValueError(
            "Invalid start or end indices for the given text: start:{start}, end: {end}"
        )

    # Extract lines and validate formatting
    result = []
    for i, line in enumerate(lines, start=1):
        if start <= i <= end:
            # Check for proper bracketing and extract the content
            match = re.match(r"<(\d+:)?(.*?)>", line)
            if not match:
                raise FormattingError(f"Invalid format for line {i}: '{line}'")
            # Add the extracted content (group 2) to the result
            if keep_brackets:
                result.append(line)
            else:
                result.append(match[2].strip())

    return "\n".join(result)
