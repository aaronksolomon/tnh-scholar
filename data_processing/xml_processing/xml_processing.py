import os
from xml.sax.saxutils import escape
from typing import List
import re
from pathlib import Path

def save_pages_to_xml(
    output_xml_path: Path,
    text_pages: List[str],
    overwrite: bool = False,
    xml_content: bool = False
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

def split_xml_pages(text, page_groups=None):
    """
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