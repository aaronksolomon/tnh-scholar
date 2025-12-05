import argparse
from pathlib import Path
from typing import Set

from lxml import etree


def extract_unique_tags(xml_file: str | Path) -> Set[str]:
    """
    Extract all unique tags from an XML file using lxml.

    Parameters:
        xml_file (str): Path to the XML file.

    Returns:
        Set[str]: A set of unique tags in the XML document.
    """
    # Parse the XML file
    tree = etree.parse(xml_file)

    # Find all unique tags and return
    return {element.tag for element in tree.iter()}


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Extract all unique tags from an XML file."
    )
    parser.add_argument("xml_file", type=str, help="Path to the XML file.")

    # Parse command-line arguments
    args = parser.parse_args()

    # Extract tags
    tags = extract_unique_tags(args.xml_file)

    # Print results
    print("Unique Tags Found:")
    for tag in sorted(tags):
        print(tag)


if __name__ == "__main__":
    main()
