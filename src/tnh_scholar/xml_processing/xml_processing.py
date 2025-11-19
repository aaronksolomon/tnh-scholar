import re
from pathlib import Path
from typing import List, Optional, Tuple
from xml.sax.saxutils import escape


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
        raise FileExistsError(
            f"The file '{output_xml_path}' already exists. Set overwrite=True to overwrite."
        )

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
                    raise ValueError(
                        f"Invalid page content at index {page_number - 1}: expected a string."
                    )

                content = text.strip()
                escaped_text = escape(content)
                xml_file.write(f"    {escaped_text}\n")
                xml_file.write(f"    <pagebreak page='{page_number}' />\n")

            # Close the root element
            xml_file.write("</document>\n")

        print(f"XML file successfully saved at {output_xml_path}")

    except PermissionError as e:
        raise PermissionError(
            f"Permission denied while writing to {output_xml_path}: {e}"
        ) from e

    except OSError as e:
        raise OSError(
            f"An OS-related error occurred while saving XML file at {output_xml_path}: {e}"
        ) from e

    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}") from e


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
        raise FileExistsError(
            f"The file {file_path} already exists and overwrite is not set."
        )

    if not data:
        raise ValueError("The data list cannot be empty.")

    # Create the XML content
    joined_data = "\n".join(data)  # Joining data with newline
    xml_content = f"<document>\n{joined_data}\n</document>"

    # Write to file
    file_path.write_text(xml_content, encoding="utf-8")


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


class PagebreakXMLParser:
    """
    Parses XML documents split by <pagebreak> tags, with optional grouping and tag retention.
    """

    def __init__(self, text: str):
        if not text or not text.strip():
            raise ValueError("Input XML text is empty or whitespace.")
        self.original_text = text
        self.cleaned_text = ""
        self.pages: List[str] = []
        self.pagebreak_tags: List[str] = []
        self._xml_decl_pattern = re.compile(r"^\s*<\?xml[^>]*\?>\s*", re.IGNORECASE)
        self._document_open_pattern = re.compile(r"^\s*<document>\s*", re.IGNORECASE)
        self._document_close_pattern = re.compile(r"\s*</document>\s*$", re.IGNORECASE)
        self._pagebreak_pattern = re.compile(r"^\s*<pagebreak\b[^>]*/>\s*$", re.IGNORECASE | re.MULTILINE)

    def _remove_preamble_and_document_tags(self):
        text = self._xml_decl_pattern.sub("", self.original_text, count=1)
        text = self._document_open_pattern.sub("", text, count=1)
        text = self._document_close_pattern.sub("", text, count=1)
        if not text.strip():
            raise ValueError("No content found between <document> tags.")
        self.cleaned_text = text

    def _split_on_pagebreaks(self):
        self.pages = []
        self.pagebreak_tags = re.findall(self._pagebreak_pattern, self.cleaned_text)
        split_lines = re.split(self._pagebreak_pattern, self.cleaned_text)
        for i, page_content in enumerate(split_lines):
            page_content = page_content.strip()
            # skip trailing empty after last pagebreak
            if not page_content and (i >= len(self.pagebreak_tags)):
                continue
            self.pages.append(page_content)

    def _attach_pagebreaks(self, keep_pagebreaks: bool):
        if not keep_pagebreaks:
            return
        for i in range(min(len(self.pages), len(self.pagebreak_tags))):
            if self.pages[i]:
                self.pages[i] = f"{self.pages[i]}\n{self.pagebreak_tags[i].strip()}"
            else:
                self.pages[i] = self.pagebreak_tags[i].strip()

    def _group_pages(self, page_groups: List[Tuple[int, int]]) -> List[str]:
        grouped_pages: List[str] = []
        for start, end in page_groups:
            if start < 1 or end < start:
                continue  # skip invalid groups
            if group := [
                self.pages[i]
                for i in range(start - 1, end)
                if 0 <= i < len(self.pages)
            ]:
                grouped_pages.append("\n".join(group).strip())
        return grouped_pages

    def parse(
        self,
        page_groups: Optional[List[Tuple[int, int]]] = None,
        keep_pagebreaks: bool = True,
    ) -> List[str]:
        """
        Parses the XML and returns a list of page contents, optionally grouped and with pagebreaks retained.
        """
        self._remove_preamble_and_document_tags()
        self._split_on_pagebreaks()
        self._attach_pagebreaks(keep_pagebreaks)
        # Remove empty pages
        self.pages = [p for p in self.pages if p]
        if not self.pages:
            raise ValueError("No pages found in the XML content after splitting on <pagebreak> tags.")
        return self._group_pages(page_groups) if page_groups else self.pages


def split_xml_on_pagebreaks(
    text: str,
    page_groups: Optional[List[Tuple[int, int]]] = None,
    keep_pagebreaks: bool = True,
) -> List[str]:
    """
    Splits an XML document into individual pages based on <pagebreak> tags.
    Optionally groups pages together based on page_groups
    and retains <pagebreak> tags if keep_pagebreaks is True.
    """
    parser = PagebreakXMLParser(text)
    return parser.parse(page_groups=page_groups, keep_pagebreaks=keep_pagebreaks)


def split_xml_pages(text: str) -> List[str]:
    """
    Backwards-compatible helper that returns the page contents without pagebreak tags.

    Args:
        text: XML document string.

    Returns:
        List of page strings.
    """
    return split_xml_on_pagebreaks(text, keep_pagebreaks=False)
