import os
from xml.sax.saxutils import escape
from typing import List
import re
from pathlib import Path
from typing import List, Optional, Tuple

class FormattingError(Exception):
    """
    Custom exception raised for formatting-related errors.
    """
    def __init__(self, message="An error occurred due to invalid formatting."):
        super().__init__(message)

def save_pages_to_xml(
    output_xml_path: Path,
    text_pages: List[str],
    overwrite: bool = False,
) -> None:
    """
    Generates and saves an XML file containing text pages, with a <pagebreak> tag indicating the page ends.
    
    Parameters:
        output_xml_path (Path): The Path object for the file where the XML file will be saved.
        text_pages (List[str]): A list of strings, each representing the text content of a page.
        overwrite (bool): If True, overwrites the file if it exists. Default is False.
    
    Returns:
        None
    
    Raises:
        ValueError: If the input list of text_pages is empty or contains invalid types.
        FileExistsError: If the file already exists and overwrite is False.
        PermissionError: If the file cannot be created due to insufficient permissions.
        OSError: For other file I/O-related errors.
    """
    if not text_pages:
        raise ValueError("The text_pages list is empty. Cannot generate XML.")

    # Check if the file exists and handle overwrite behavior
    if output_xml_path.exists() and not overwrite:
        raise FileExistsError(f"The file '{output_xml_path}' already exists. Set overwrite=True to overwrite.")

    try:
        # Ensure the output directory exists
        output_xml_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the XML file
        with output_xml_path.open("w", encoding="utf-8") as xml_file:
            # Write XML declaration and root element
            xml_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            xml_file.write("<document>\n")

            # Add each page with its content and <pagebreak> tag
            for page_number, text in enumerate(text_pages, start=1):
                if not isinstance(text, str):
                    raise ValueError(f"Invalid page content at index {page_number - 1}: expected a string.")
                
                content = text.strip()
                escaped_text = escape(content)
                xml_file.write(f"    {escaped_text}\n")
                xml_file.write(f"    <pagebreak page='{page_number}' />\n")

            # Close the root element
            xml_file.write("</document>\n")

        print(f"XML file successfully saved at {output_xml_path}")

    except PermissionError as e:
        raise PermissionError(f"Permission denied while writing to {output_xml_path}: {e}")

    except OSError as e:
        raise OSError(f"An OS-related error occurred while saving XML file at {output_xml_path}: {e}")

    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")

def join_xml_data_to_doc(
    file_path: Path, data: List[str], overwrite: bool = False
) -> None:
    """
    Joins a list of XML-tagged data with newlines, wraps it with <document> tags, 
    and writes it to the specified file. Raises an exception if the file exists 
    and overwrite is not set.

    Args:
        file_path (Path): Path to the output file.
        data (List[str]): List of XML-tagged data strings.
        overwrite (bool): Whether to overwrite the file if it exists.

    Raises:
        FileExistsError: If the file exists and overwrite is False.
        ValueError: If the data list is empty.

    Example:
        >>> join_xml_data_to_doc(Path("output.xml"), ["<tag>Data</tag>"], overwrite=True)
    """
    if file_path.exists() and not overwrite:
        raise FileExistsError(f"The file {file_path} already exists and overwrite is not set.")
    
    if not data:
        raise ValueError("The data list cannot be empty.")
    
    # Create the XML content
    joined_data = "\n".join(data)  # Joining data with newline
    xml_content = f"<document>\n{joined_data}\n</document>"
    
    # Write to file
    file_path.write_text(xml_content, encoding='utf-8')

def remove_page_tags(text):
    """
    Removes <page ...> and </page> tags from a text string.

    Parameters:
    - text (str): The input text containing <page> tags.

    Returns:
    - str: The text with <page> tags removed.
    """
    # Remove opening <page ...> tags
    text = re.sub(r"<page[^>]*>", "", text)
    # Remove closing </page> tags
    text = re.sub(r"</page>", "", text)
    return text

from typing import List, Optional, Tuple

def split_xml_on_pagebreaks(
    text: str,
    page_groups: Optional[List[Tuple[int, int]]] = None,
    keep_pagebreaks: bool = True,
) -> List[str]:
    """
    Splits an XML document into individual pages based on <pagebreak> tags.
    Optionally groups pages together based on page_groups and retains <pagebreak> tags if keep_pagebreaks is True.

    Parameters:
        text (str): The XML document as a string.
        page_groups (Optional[List[Tuple[int, int]]]): A list of tuples defining page ranges to group together.
                                                      Each tuple is of the form (start_page, end_page), inclusive.
        keep_pagebreaks (bool): Whether to retain the <pagebreak> tags in the returned data. Default is False.

    Returns:
        List[str]: A list of page contents as strings, either split by pages or grouped by page_groups.

    Raises:
        ValueError: If the expected preamble or <document> tags are missing.
    """
    # Split text into lines
    lines = text.splitlines()

    # Preprocess: Remove `<?xml ... ?>` preamble and <document> tags
    if lines[0].startswith("<?xml"):
        lines.pop(0)
    else:
        raise ValueError("Missing `<?xml ... ?>` preamble on the first line.")
    if lines[0].strip() == "<document>":
        lines.pop(0)
    else:
        raise ValueError("Missing `<document>` opening tag on the second line.")
    if lines[-1].strip() == "</document>":
        lines.pop(-1)
    else:
        raise ValueError("Missing `</document>` closing tag on the last line.")

    # Process content to split pages based on <pagebreak> tags
    pages = []
    current_page = []

    for line in lines:
        if "<pagebreak" in line:  # Page boundary detected
            if current_page:
                page_content = "\n".join(current_page).strip()
                if keep_pagebreaks:
                    page_content += f"\n{line.strip()}"  # Retain the <pagebreak> tag
                pages.append(page_content)
                current_page = []
        else:
            current_page.append(line)

    # Append the last page if it exists
    if current_page:
        pages.append("\n".join(current_page).strip())

    # Validate that pages are extracted
    if not pages:
        raise ValueError("No pages found in the XML content.")

    # Group pages if page_groups is provided
    if page_groups:
        grouped_pages = []
        for start, end in page_groups:
            group_content = []
            for i in range(start - 1, end):  # Page numbers are 1-based, so adjust to 0-based indexing
                if 0 <= i < len(pages):  # Ensure the index is within bounds
                    group_content.append(pages[i])
            if group_content:
                grouped_pages.append("\n".join(group_content).strip())
        return grouped_pages

    return pages

# cleaning helper functions:
def wrap_lines(text: str, number: bool = False) -> str:
    """
    Encloses each line of the input text with angle brackets.
    If number is True, adds a line number followed by a colon `:` and then the line.

    Args:
        text (str): The input string containing lines separated by '\n'.
        number (bool): Whether to prepend line numbers to each line.

    Returns:
        str: A string where each line is enclosed in angle brackets.
    
    Examples:
        >>> wrap_lines("This is a string with\n   two lines.")
        '<This is a string with>\n<   two lines.>'

        >>> wrap_lines("This is a string with\n   two lines.", number=True)
        '<1:This is a string with>\n<2:   two lines.>'
    """
    return '\n'.join(
        f"<{f'{i+1}:{line}' if number else line}>"
        for i, line in enumerate(text.split('\n'))
    )

def wrap_all_lines(pages):
    return [wrap_lines(page) for page in pages]

def unwrap_lines(text: str, number: bool = False) -> str:
    """
    Removes angle brackets (< >) from encapsulated lines and optionally removes line numbers.

    Args:
        text (str): The input string with encapsulated lines.
        number (bool): If True, removes line numbers in the format 'digit:'. 
                       Raises a ValueError if `number=True` and a line does not start with a digit followed by a colon.

    Returns:
        str: A newline-separated string with the encapsulation removed, and line numbers stripped if specified.

    Examples:
        >>> unwrap_lines("<1:Line 1>\n<2:Line 2>", number=True)
        'Line 1\nLine 2'

        >>> unwrap_lines("<Line 1>\n<Line 2>")
        'Line 1\nLine 2'

        >>> unwrap_lines("<1Line 1>", number=True)
        ValueError: Line does not start with a valid number: '1Line 1'
    """
    unwrapped_lines = []

    for line in text.splitlines():
        match = re.match(r"<(\d+):(.*?)>", line) if number else re.match(r"<(.*?)>", line)
        if match:
            content = match.group(2).strip() if number else match.group(1).strip()
            unwrapped_lines.append(content)
        else:
            if number:
                raise FormattingError(f"Line does not start with a valid number: '{line}'")
            else:
                raise FormattingError(f"Line does not follow the expected format: '{line}'")
    
    return "\n".join(unwrapped_lines)

def unwrap_all_lines(pages):
    result = []
    for page in pages:
        if page == "blank page":
            result.append(page)
        else:
            result.append(unwrap_lines(page))
    return result

def lines_from_wrapped_text(text: str, start: int, end: int, keep_brackets=False) -> list[str]:
    """
    Extracts lines from wrapped text between the start and end indices, inclusive.
    Handles both numbered and non-numbered cases.
    
    Args:
        text (str): The input wrapped text containing lines like <...>.
        start (int): The starting line number (1-based).
        end (int): The ending line number (1-based).
    
    Returns:
        list[str]: The lines from start to end inclusive, with angle brackets removed.
    
    Raises:
        FormattingError: If the text contains improperly formatted lines (missing angle brackets).
        ValueError: If start or end indices are invalid or out of bounds.
    
    Examples:
        >>> text = "<1:Line 1>\n<2:Line 2>\n<3:Line 3>"
        >>> lines_from_wrapped_text(text, 1, 2)
        ['Line 1', 'Line 2']
        
        >>> text = "<Line 1>\n<Line 2>\n<Line 3>"
        >>> lines_from_wrapped_text(text, 2, 3)
        ['Line 2', 'Line 3']
    """
    # Split the text into lines
    lines = text.splitlines()
    
    # Validate indices
    if start < 1 or end < 1 or start > end or end > len(lines):
        raise ValueError("Invalid start or end indices for the given text: start:{start}, end: {end}")

    # Extract lines and validate formatting
    result = []
    for i, line in enumerate(lines, start=1):
        if start <= i <= end:
            # Check for proper wrapping and extract the content
            match = re.match(r"<(\d+:)?(.*?)>", line)
            if not match:
                raise FormattingError(f"Invalid format for line {i}: '{line}'")
            # Add the extracted content (group 2) to the result
            if keep_brackets:
                result.append(line)
            else:
                result.append(match.group(2).strip())
    
    return "\n".join(result)

def split_xml_pages(text, page_groups=None):
    """
    DEPRICATED: use split_xml_on_pagebreaks

    Splits an XML document into individual pages based on <page> tags.
    Optionally groups pages together based on page_groups.

    Parameters:
    - text (str): The XML document as a string.
    - page_groups (list of tuples, optional): A list of tuples defining page ranges to group together.
                                              Each tuple is of the form (start_page, end_page), inclusive.

    Returns:
    - List[str]: A list of strings, where each element is a single page (if no groups) or a group of pages.
    """
    from lxml import etree

    # Parse the XML text into an element tree
    try:
        root = etree.fromstring(text.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        # Handle parsing errors with helpful debugging information
        line_number = e.lineno
        column_number = e.offset
        lines = text.splitlines()
        error_line = lines[line_number - 1] if line_number - 1 < len(lines) else "Unknown line"
        print(f"XMLSyntaxError: {e}")
        print(f"Offending line {line_number}, column {column_number}: {error_line}")
        return []  # Return an empty list if parsing fails

    # Extract all pages as a list of strings
    pages = [
        (int(page.get("page")), etree.tostring(page, encoding="unicode"))
        for page in root.findall(".//page")
    ]
    
    # Sort pages by page number
    pages.sort(key=lambda x: x[0])

    # If no page_groups, return individual pages
    if not page_groups:
        return [content for _, content in pages]

    # Group pages based on page_groups
    grouped_pages = []
    for start, end in page_groups:
        group_content = ""
        for page_num, content in pages:
            if start <= page_num <= end:
                group_content += content
        if group_content:
            grouped_pages.append(group_content)

    return grouped_pages