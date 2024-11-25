import os
from xml.sax.saxutils import escape
from typing import List

def save_pages_to_xml(text_pages: List[str], output_xml_path: str, overwrite: bool = False) -> None:
    """
    Generates and saves an XML file containing text pages, with an option to overwrite existing files.

    Parameters:
        text_pages (List[str]): A list of strings, each representing the text content of a page.
        output_xml_path (str): The full file path where the XML file will be saved.
        overwrite (bool): If True, overwrites the file if it exists. Default is False.

    Returns:
        None

    Raises:
        ValueError: If the input list of text_pages is empty.
        FileExistsError: If the file already exists and overwrite is False.
        OSError: If there's an issue creating directories or saving the XML file.
    """
    if not text_pages:
        raise ValueError("The text_pages list is empty. Cannot generate XML.")

    # Check if the file exists and handle overwrite behavior
    if os.path.exists(output_xml_path) and not overwrite:
        raise FileExistsError(f"The file '{output_xml_path}' already exists. Set overwrite=True to overwrite.")

    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_xml_path), exist_ok=True)

        # Write the XML file
        with open(output_xml_path, "w", encoding="utf-8") as xml_file:
            # Write XML declaration and root element
            xml_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            xml_file.write("<document>\n")

            # Add each page with its content, escaping special characters for XML safety
            for page_number, text in enumerate(text_pages, start=1):
                escaped_text = escape(text.strip()) if text.strip() else ""
                xml_file.write(f"  <page page='{page_number}'>\n")
                xml_file.write(f"    {escaped_text}\n")
                xml_file.write("  </page>\n")

            # Close the root element
            xml_file.write("</document>\n")

        print(f"XML file successfully saved at {output_xml_path}")

    except OSError as e:
        raise OSError(f"Error saving XML file at {output_xml_path}: {e}")