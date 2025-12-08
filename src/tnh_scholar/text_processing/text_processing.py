import re


def normalize_newlines(text: str, spacing: int = 2) -> str:
    """
    Normalize newline blocks in the input text by reducing consecutive newlines
    to the specified number of newlines for consistent readability and formatting.

    Parameters:
    ----------
    text : str
        The input text containing inconsistent newline spacing.
    spacing : int, optional
        The number of newlines to insert between lines. Defaults to 2.

    Returns:
    -------
    str
        The text with consecutive newlines reduced to the specified number of newlines.

    Example:
    --------
    >>> raw_text = "Heading\n\n\nParagraph text 1\nParagraph text 2\n\n\n"
    >>> normalize_newlines(raw_text, spacing=2)
    'Heading\n\nParagraph text 1\n\nParagraph text 2\n\n'
    """
    # Replace one or more newlines with the desired number of newlines
    newlines = "\n" * spacing
    return re.sub(r"\n{1,}", newlines, text)

def clean_text(text: str, newline: bool = False) -> str:
    """
    Cleans a given text by replacing specific unwanted characters such as
    tab, and non-breaking spaces with regular spaces.

    This function takes a string as input and applies replacements
    based on a predefined mapping of characters to replace.

    Args:
        text (str): The text to be cleaned.

    Returns:
        str: The cleaned text with unwanted characters replaced by spaces.

    Example:
        >>> text = "This is\\n an example\\ttext with\\xa0extra spaces."
        >>> clean_text(text)
        'This is an example text with extra spaces.'

    """
    # Define a mapping of characters to replace
    replace_map = {
        "\t": " ",  # Replace tabs with space
        "\xa0": " ",  # Replace non-breaking space with regular space
        # Add more replacements as needed
    }

    if newline:
        replace_map["\n"] = ""  # remove newlines

    # Loop through the replace map and replace each character
    for old_char, new_char in replace_map.items():
        text = text.replace(old_char, new_char)

    return text.strip()  # Ensure any leading/trailing spaces are removed
