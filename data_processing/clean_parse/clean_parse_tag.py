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
    >>> raw_text = "Heading\n\n\nParagraph text 1\n\nParagraph text 2\n\n\n"
    >>> normalize_newlines(raw_text, spacing=2)
    'Heading\n\nParagraph text 1\n\nParagraph text 2\n\n'
    """
    # Replace two or more newlines with the desired number of newlines
    newlines = '\n' * spacing
    return re.sub(r'\n{2,}', newlines, text)

import os

# Global variable for storing the working directory
working_directory = None

def set_working_directory(directory: str) -> None:
    """
    Sets the global working directory to the specified path.

    Parameters:
    ----------
    directory : str
        The path to the directory to be set as the working directory.
    """
    global working_directory
    if os.path.isdir(directory):
        working_directory = directory
    else:
        raise ValueError(f"The directory '{directory}' does not exist or is not a valid directory.")

def get_text_from_file(file_path: str) -> str:
    """
    Reads the entire content of a text file, looking first in the global working 
    directory if set, otherwise in the current working directory.

    Parameters:
    ----------
    file_path : str
        The name or relative path to the text file.

    Returns:
    -------
    str
        The content of the text file as a single string.

    Example:
    --------
    >>> set_working_directory("/path/to/directory")
    >>> text = get_text_from_file("example.txt")
    >>> print(text)
    'This is the content of the file.'
    """
    global working_directory
    
    # If a working directory is set, look for the file there
    if working_directory:
        full_path = os.path.join(working_directory, file_path)
    else:
        # Otherwise, just use the file path directly
        full_path = file_path

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"The file '{full_path}' does not exist.")
    
    with open(full_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def write_text_to_file(file_path: str, content: str) -> None:
    """
    Writes the given content to a text file, saving it in the global working 
    directory if set, otherwise in the current working directory.

    Parameters:
    ----------
    file_path : str
        The name or relative path of the text file to write.
    content : str
        The content to be written to the file.

    Example:
    --------
    >>> set_working_directory("/path/to/directory")
    >>> write_text_to_file("example.txt", "This is some content.")
    """
    global working_directory
    
    # If a working directory is set, use it; otherwise, use the file path as given
    if working_directory:
        full_path = os.path.join(working_directory, file_path)
    else:
        full_path = file_path

    # Write the content to the specified file
    with open(full_path, 'w', encoding='utf-8') as file:
        file.write(content)

def clean_text(text):
    """
    Cleans a given text by replacing specific unwanted characters such as 
    newline, tab, and non-breaking spaces with regular spaces.

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
        '\n': ' ',       # Replace newlines with space
        '\t': ' ',       # Replace tabs with space
        '\xa0': ' ',     # Replace non-breaking space with regular space
        # Add more replacements as needed
    }

    # Loop through the replace map and replace each character
    for old_char, new_char in replace_map.items():
        text = text.replace(old_char, new_char)
    
    return text.strip()  # Ensure any leading/trailing spaces are removed

## tag work

from bs4 import BeautifulSoup

def extract_tags_by_attributes(soup: BeautifulSoup, tags_with_attributes: dict[str, dict]) -> dict[tuple[str, tuple], list[BeautifulSoup]]:
    """
    Extract specified tags and their attributes from a BeautifulSoup object.

    This function allows you to search for multiple tags and their respective attributes
    within an HTML document parsed by BeautifulSoup. The result is a dictionary where
    each key is a tuple `(tag, attribute_values)` representing the tag name and the
    attributes used to search for that tag. The corresponding value is a list of the
    matching tags found in the soup object.

    Parameters:
    -----------
    soup : BeautifulSoup
        The parsed HTML content from which tags will be extracted.
        
    tags_with_attributes : dict
        A dictionary where keys are the tag names (e.g., 'p', 'span') and values are
        attribute dictionaries that filter the tags. For example, {'p': {}, 'span': {'class': 'italic'}}.
        - To search for a tag without any attribute filters, provide an empty dictionary `{}`.

    Returns:
    --------
    dict
        A dictionary where each key is a tuple `(tag, attribute_values)`:
            - `tag`: The HTML tag name (e.g., 'p', 'span').
            - `attribute_values`: A tuple of key-value pairs representing the tag's attributes (e.g., `(('class', 'italic'),)`).
              If no attributes were specified, the tuple will be empty `()`.
        The corresponding value is a list of BeautifulSoup tag elements that matched the search criteria.

    Example:
    --------
    >>> soup = BeautifulSoup('<p>This is a paragraph.</p><span class="italic">Italic text</span>', 'html.parser')
    >>> tags_to_find = {'p': {}, 'span': {'class': 'italic'}}
    >>> extracted = extract_tags_by_attributes(soup, tags_to_find)
    >>> for (tag, attributes), matches in extracted.items():
    >>>     print(f"Found {len(matches)} {tag} tags with attributes {attributes}.")
    
    Example Output:
    ---------------
    Found 1 p tags with attributes ().
    Found 1 span tags with attributes (('class', 'italic'),).
    """
    
    extracted_tags = {}
    
    # Loop over each tag and attribute specification
    for tag, attributes in tags_with_attributes.items():
        # Use find_all to search for tags with the specified attributes
        matching_tags = soup.find_all(tag, attrs=attributes)
        
        # Store results using (tag, attribute_values) as key
        if attributes:
            extracted_tags[(tag, tuple(attributes.items()))] = matching_tags
        else:
            # No attributes; use an empty tuple for the key
            extracted_tags[(tag, ())] = matching_tags
    
    return extracted_tags

def get_all_tag_names(soup: BeautifulSoup) -> list[str]:
    """
    Extract all unique HTML tag names from a BeautifulSoup object.

    Parameters:
    -----------
    soup : BeautifulSoup
        The parsed HTML content.

    Returns:
    --------
    list[str]
        A list of all unique tag names in the soup, without content.
    
    Example:
    --------
    >>> soup = BeautifulSoup('<p>Paragraph</p><div><span>Text</span></div>', 'html.parser')
    >>> get_all_tag_names(soup)
    ['p', 'div', 'span']
    """
    return list(set([tag.name for tag in soup.find_all(True)]))

# # Example usage:
# soup = BeautifulSoup('<p>Paragraph</p><div><span>Text</span></div>', 'html.parser')
# all_tags = get_all_tag_names(soup)
# print(all_tags)

def get_all_attribute_values(soup: BeautifulSoup, tag: str) -> dict[str, set[str]]:
    """
    Extract all unique attribute-value pairs for a given HTML tag across the soup.
    
    For each attribute of the specified tag, store a set of all unique values 
    found across all occurrences of that tag in the soup.

    Parameters:
    -----------
    soup : BeautifulSoup
        The parsed HTML content.
    
    tag : str
        The tag name to search for (e.g., 'span', 'div').

    Returns:
    --------
    dict[str, set[str]]
        A dictionary where keys are attribute names and values are sets of 
        unique attribute values across all instances of the given tag.
    
    Example:
    --------
    >>> soup = BeautifulSoup('''
    ... <p class="text" id="para1">Paragraph</p>
    ... <p class="text" id="para2" style="color:red;">Styled paragraph</p>
    ... <p class="highlight" id="para2" style="color:blue;">Another paragraph</p>''', 'html.parser')
    >>> get_all_attribute_values(soup, 'p')
    {'class': {'text', 'highlight'}, 'id': {'para1', 'para2'}, 'style': {'color:red;', 'color:blue;'}}
    """
    attributes_with_values = {}

    # Find all instances of the specified tag
    for element in soup.find_all(tag):
        # Loop through each attribute in the element's attributes
        for attr, value in element.attrs.items():
            # Add the attribute to the dictionary if not already present
            if attr not in attributes_with_values:
                attributes_with_values[attr] = set()
            # Add the value to the set of values for the attribute
            attributes_with_values[attr].add(value)

    return attributes_with_values

