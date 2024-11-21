import re
import os
from bs4 import BeautifulSoup
from bs4 import NavigableString, Tag
from typing import Union
import warnings

# Global variable for storing the working directory for input and output data in the TNH Scholar project
tnh_scholar_working_dir = None

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

def set_working_directory(directory: str) -> None:
    """
    Sets the global working directory to the specified path.

    Parameters:
    ----------
    directory : str
        The path to the directory to be set as the working directory.
    """
    global tnh_scholar_working_dir
    if os.path.isdir(directory):
        tnh_scholar_working_dir = directory
    else:
        raise ValueError(f"The directory '{directory}' does not exist or is not a valid directory.")
    
def get_working_directory():
    """
    Get the global working directory 

    Parameters:
    ----------
    None
        
    Returns:
    --------        
    The path to thworking directory.
    """
    global tnh_scholar_working_dir

    return tnh_scholar_working_dir

def get_text_from_file(file_path: str, search_path: str = None) -> str:
    """
    Reads the entire content of a text file, looking first in the specified directory 
    if provided, then in the global working directory if set, otherwise in the current working directory.

    Parameters:
    ----------
    file_path : str
        The name or relative path to the text file.
    search_path : str, optional
        The directory path to look for the file. If specified, it overrides 
        the global working directory and the current working directory.

    Returns:
    -------
    str
        The content of the text file as a single string.

    Example:
    --------
    >>> set_working_directory("/path/to/directory")
    >>> text = get_text_from_file("example.txt", dir="/another/path")
    >>> print(text)
    'This is the content of the file.'
    """
    global tnh_scholar_working_dir
    
    # Determine the directory to use
    if search_path:
        full_path = os.path.join(search_path, file_path)
    elif tnh_scholar_working_dir:
        full_path = os.path.join(tnh_scholar_working_dir, file_path)
    else:
        full_path = file_path

    # Check if the file exists
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"The file '{full_path}' does not exist.")
    
    # Read and return the content of the file
    with open(full_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def write_text_to_file(file_path: str, content: str, force: bool = False) -> None:
    """
    Writes the given content to a text file. Saves the file in the global 
    working directory if set, otherwise in the current working directory. 
    Checks if the file already exists and raises a warning if it does, unless 
    force=True is specified to overwrite.

    Parameters:
    ----------
    file_path : str
        The name or relative path of the text file to write.
    content : str
        The content to be written to the file.
    force : bool, optional
        If True, overwrite the file if it exists. Default is False.

    Raises:
    ------
    FileExistsWarning
        If the file already exists and force is set to False.
    OSError
        If the file cannot be written due to I/O errors.

    Example:
    --------
    >>> set_working_directory("/path/to/directory")
    >>> write_text_to_file("example.txt", "This is some content.", force=True)
    """
    global tnh_scholar_working_dir

    # Determine the full path based on the working directory
    full_path = os.path.join(tnh_scholar_working_dir, file_path) if tnh_scholar_working_dir else file_path

    # Check if the file exists and warn if not overwriting
    if os.path.exists(full_path) and not force:
        warnings.warn(f"The file '{full_path}' already exists. Use force=True to overwrite.", FileExistsWarning)
        return

    try:
        # Write the content to the specified file
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except OSError as e:
        raise OSError(f"Failed to write to file '{full_path}'.") from e

def clean_text(text, newline=False):
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
        '\t': ' ',       # Replace tabs with space
        '\xa0': ' ',     # Replace non-breaking space with regular space
        # Add more replacements as needed
    }

    if newline:
        replace_map['\n'] = '' # remove newlines

    # Loop through the replace map and replace each character
    for old_char, new_char in replace_map.items():
        text = text.replace(old_char, new_char)
    
    return text.strip()  # Ensure any leading/trailing spaces are removed

## tag work

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
            # Check if the value is a list (e.g., class="class1 class2") and handle accordingly
            if isinstance(value, list):
                attributes_with_values[attr].update(value)  # Add all elements from the list
            else:
                attributes_with_values[attr].add(value)  # Add a single value

    return attributes_with_values

def remove_all_tags_with_attribute(soup: BeautifulSoup, attr_name: str, attr_value_pattern: str = None) -> None:
    """
    Remove unwanted tags with specific attributes from a BeautifulSoup object.
    
    This function removes tags with a specific attribute (e.g., 'class') that matches a regular expression pattern.
    

    Parameters:
    -----------
    soup : BeautifulSoup
        The parsed HTML content to clean.
    
    attr_name : str
        The attribute name to match (e.g., 'class', 'id'). If None, no attribute filtering is done.
    
    attr_value_pattern : str, optional
        A regular expression pattern to match attribute values. Only tags whose specified attribute 
        matches this pattern will be removed. If None, the function removes all tags with the specified attribute.
    
    Returns:
    --------
    None
        The function modifies the BeautifulSoup object in place, removing the unwanted tags or attributes.

    Example:
    --------
    >>> soup = BeautifulSoup('<div class="calibre1">Text</div><p class="keep">Keep me</p>', 'html.parser')
    >>> remove_all_tags_with_attribute(soup, attr_name='class', attr_value_pattern=r'calibre.*')
    >>> print(soup)
    <p class="keep">Keep me</p>
    """
    
    tags_to_remove = []

    # Find all tags in the soup
    for element in soup.find_all(True):
        # If an attribute name is specified, filter tags by the attribute
        if attr_name in element.attrs:
            attr_value = element[attr_name]
            if attr_value_pattern:
                # If there's a pattern, check for a match
                if isinstance(attr_value, list):
                    # Check if any value in the list matches the pattern
                    if any(re.match(attr_value_pattern, val) for val in attr_value):
                        tags_to_remove.append(element)
                else:
                    # If it's a string, check the pattern directly
                    if re.match(attr_value_pattern, attr_value):
                        tags_to_remove.append(element)
        elif not attr_name:
            # If no attribute is specified, remove the entire tag
            tags_to_remove.append(element)

    # Remove all collected tags
    for tag in tags_to_remove:
        tag.decompose()

def remove_tags_with_attribute(soup: BeautifulSoup, tag_list: Union[list[str], str], attr_name: str, attr_value_pattern: str = None) -> None:
    """
    Remove a specific tags with specific attributes from a BeautifulSoup object.
    
    This function removes tags with a specific attribute (e.g., 'class') that matches a regular expression pattern.
    

    Parameters:
    -----------
    soup : BeautifulSoup
        The parsed HTML content to clean.

    tag_list : the list of tags to remove if matchin attribute is found; if a single string, then this string is split into tags.
    
    attr_name : str
        The attribute name to match (e.g., 'class', 'id'). If None, no attribute filtering is done.
    
    attr_value_pattern : str, optional
        A regular expression pattern to match attribute values. Only tags whose specified attribute 
        matches this pattern will be removed. If None, the function removes all tags with the specified attribute.
    
    Returns:
    --------
    None
        The function modifies the BeautifulSoup object in place, removing the unwanted tags or attributes.

    Example:
    --------
    >>> soup = BeautifulSoup('<div class="calibre1">Text</div><p class="keep">Keep me</p>', 'html.parser')
    >>> remove_tags_with_attribute(soup, 'div', 'class', attr_value_pattern=r'calibre.*')
    >>> print(soup)
    <p class="keep">Keep me</p>
    """

    if isinstance(tag_list, str):
        tag_list = tag_list.split()

    tags_to_remove = []

    # Find all tags in the soup
    for element in soup.find_all(*tag_list):
        # If an attribute name is specified, filter tags by the attribute
        if attr_name in element.attrs:
            attr_value = element[attr_name]
            if attr_value_pattern:
                # If there's a pattern, check for a match
                if isinstance(attr_value, list):
                    # Check if any value in the list matches the pattern
                    if any(re.match(attr_value_pattern, val) for val in attr_value):
                        tags_to_remove.append(element)
                else:
                    # If it's a string, check the pattern directly
                    if re.match(attr_value_pattern, attr_value):
                        tags_to_remove.append(element)
        elif not attr_name:
            # If no attribute is specified, remove the entire tag
            tags_to_remove.append(element)

    # Remove all collected tags
    for tag in tags_to_remove:
        tag.decompose()

def remove_attributes(soup: BeautifulSoup, attr_name: str, attr_value_pattern: str = None, tag: str = None) -> None:
    """
    Remove unwanted attributes from a specific tag or all tags in a BeautifulSoup object.

    This function removes attributes based on the tag name and/or attribute value pattern. It can:
    - Remove attributes from a specific tag (e.g., 'div').
    - Remove attributes with a specific attribute value that matches a regular expression pattern.
    - Remove attributes from all tags if no specific tag is provided.

    Parameters:
    -----------
    soup : BeautifulSoup
        The parsed HTML content to clean.
    
    attr_name : str
        The attribute name to remove (e.g., 'class', 'id').
    
    attr_value_pattern : str, optional
        A regular expression pattern to match attribute values. Only attributes whose values
        match this pattern will be removed. If None, the attribute will be removed unconditionally.

    tag : str, optional
        The tag name to filter by (e.g., 'div', 'span'). If None, the attribute will be removed 
        from all tags that have the specified attribute.

    Returns:
    --------
    None
        The function modifies the BeautifulSoup object in place, removing the unwanted attributes.

    Example:
    --------
    >>> soup = BeautifulSoup('<div class="calibre1">Text</div><p class="keep">Keep me</p>', 'html.parser')
    >>> remove_attributes(soup, attr_name='class', attr_value_pattern=r'calibre.*')
    >>> print(soup)
    <div>Text</div><p class="keep">Keep me</p>
    """
    
    # Find all tags, filtered by tag name if provided
    for element in soup.find_all(tag or True):
        # Check if the tag has the specified attribute
        if attr_name in element.attrs:
            attr_value = element[attr_name]
            
            # Check if we are matching the attribute value against a pattern
            if attr_value_pattern:
                # If the attribute value is a list (e.g., for class attribute), handle that case
                if isinstance(attr_value, list):
                    # Remove the attribute if any value in the list matches the pattern
                    if any(re.match(attr_value_pattern, val) for val in attr_value):
                        del element[attr_name]
                else:
                    # For single values, remove the attribute if it matches the pattern
                    if re.match(attr_value_pattern, attr_value):
                        del element[attr_name]
            else:
                # If no pattern is specified, remove the attribute unconditionally
                del element[attr_name]

from bs4 import BeautifulSoup
from bs4.element import NavigableString
import copy

def generate_reduced_text_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Creates a copy of a BeautifulSoup object and truncates the text content of all NavigableString 
    elements in the copied BeautifulSoup object to the first five words, appending ellipses ("...") 
    if the text contains more than five words. The function returns a new BeautifulSoup object, 
    leaving the original unmodified.

    Parameters:
    -----------
    soup : BeautifulSoup
        A BeautifulSoup object representing the parsed HTML or XML content.

    Returns:
    --------
    BeautifulSoup
        A new BeautifulSoup object with truncated text.

    Example:
    --------
    >>> from bs4 import BeautifulSoup
    >>> html_content = "<p>This is a paragraph with more than five words.</p>"
    >>> soup = BeautifulSoup(html_content, 'html.parser')
    >>> result = reduce_tags_and_text(soup)
    >>> print(result.prettify())
    <p>This is a paragraph with ...</p>

    Notes:
    ------
    - Only NavigableString elements (text nodes) are truncated. HTML tags and structure remain unchanged.
    - The function does not remove or alter tags but only modifies the text within the tags.
    - The original BeautifulSoup object is left unchanged.
    """
    # Create a deep copy of the soup object to avoid modifying the original
    new_soup = copy.deepcopy(soup)

    # Traverse through all elements in the copied soup, targeting text nodes
    for element in new_soup.find_all(string=True):  # Find all NavigableString text nodes
        if isinstance(element, NavigableString):
            words = element.split()
            if len(words) > 5:
                truncated_text = ' '.join(words[:5]) + " ..."
                # Replace the text with the truncated version in the copied soup
                element.replace_with(truncated_text)

    return new_soup  # Return the modified copy of the soup object

def tag_has_visible_text(tag) -> bool:
    """
    Check if a BeautifulSoup tag has visible text content, meaning it contains text that is not 
    solely whitespace.

    This function is useful for determining whether a tag has meaningful text content, as opposed to 
    being empty or containing only whitespace. 

    Parameters:
    -----------
    tag : BeautifulSoup tag
        The BeautifulSoup tag to check for visible text content.

    Returns:
    --------
    bool
        True if the tag contains visible text (after stripping whitespace), otherwise False.

    Example:
    --------
    >>> from bs4 import BeautifulSoup
    >>> html_content = "<div>   </div><p>This is text content.</p>"
    >>> soup = BeautifulSoup(html_content, 'html.parser')
    >>> div_tag = soup.find('div')
    >>> tag_has_visible_text(div_tag)
    False

    >>> p_tag = soup.find('p')
    >>> tag_has_visible_text(p_tag)
    True

    Notes:
    ------
    - This function ignores any nested tags, focusing only on direct visible text content.
    - Whitespace-only content is considered empty and will return False.
    """
    return bool(tag.get_text(strip=True))

def tag_has_descendants(tag) -> bool:
    """
    Check if a BeautifulSoup tag has any descendants (nested elements), such as child tags 
    or text nodes.

    This function is useful for determining if a tag contains any nested structure, whether 
    directly or indirectly, as opposed to being a standalone empty tag.

    Parameters:
    -----------
    tag : BeautifulSoup tag
        The BeautifulSoup tag to check for descendants.

    Returns:
    --------
    bool
        True if the tag contains any descendants (nested tags or text nodes), otherwise False.

    Example:
    --------
    >>> from bs4 import BeautifulSoup
    >>> html_content = "<div><p>Text inside paragraph.</p></div>"
    >>> soup = BeautifulSoup(html_content, 'html.parser')
    >>> div_tag = soup.find('div')
    >>> tag_has_descendants(div_tag)
    True
    
    >>> empty_tag = soup.new_tag('div')
    >>> tag_has_descendants(empty_tag)
    False

    Notes:
    ------
    - This function checks if there are any nested tags or text nodes within the tag,
      regardless of depth. If the tag has even a single nested element, it returns True.
    - Ideal for use in filtering or cleaning HTML where nested structures are significant.
    """
    return any(tag.descendants)

def remove_empty_tags(soup: BeautifulSoup, tag_list) -> None:
    """
    Remove empty tags from a BeautifulSoup object based on a specified list or space-separated string of tag names.
    
    This function examines each specified tag and checks if it is empty (contains no visible text).
    If a tag contains only nested elements (i.e., descendants) but no visible text, it will be unwrapped
    (preserving the nested content). Tags that contain neither text nor descendants are completely removed
    from the document.

    Parameters:
    -----------
    soup : BeautifulSoup
        The parsed HTML or XML content to clean.
    
    tag_list : list or str
        A list of tag names (e.g., ['div', 'a']) or a space-separated string (e.g., 'div a') specifying
        which tags should be checked and removed if empty. Only tags matching these names will be considered.
    
    Returns:
    --------
    None
        This function modifies the BeautifulSoup object in place, removing or unwrapping tags as needed.

    Example:
    --------
    >>> from bs4 import BeautifulSoup
    >>> html_content = "<div></div><a href='link'><span></span></a><p>Content</p>"
    >>> soup = BeautifulSoup(html_content, 'html.parser')
    >>> remove_empty_tags(soup, 'div a')
    >>> print(soup)
    <span></span><p>Content</p>

    Notes:
    ------
    - This function relies on two helper functions, `tag_has_visible_text` and `tag_has_descendants`:
        - `tag_has_visible_text(tag)`: Returns True if the tag contains visible text (ignoring whitespace).
        - `tag_has_descendants(tag)`: Returns True if the tag has nested elements (descendants).
    - The function operates in place, meaning it directly modifies the `soup` object passed to it.
    - Tags with descendants but no visible text are unwrapped rather than removed, ensuring that nested 
      content remains intact.
    - Useful for cleaning up HTML or XML content by removing purely empty elements without affecting structure.
    """
    
    # Ensure tag_list is a list, even if passed as a space-separated string
    if isinstance(tag_list, str):
        tag_list = tag_list.split()

    # Process tags in tag_list to either unwrap or remove
    for tag_name in tag_list:
        for tag in soup.find_all(tag_name):
            # Check if the tag is empty (no text content) and has no nested elements
            if not tag_has_visible_text(tag):
                if tag_has_descendants(tag):
                    # Tag has descendants, so unwrap it instead of decomposing
                    tag.unwrap()
                else:
                    # Tag is truly empty of meaningful content, so decompose it
                    tag.decompose()

def unwrap_redundant_tags(soup: BeautifulSoup, tag_list) -> None:
    """
    Unwrap tags that do not have any attributes and contain only a single child tag, 
    by first collecting tags to unwrap, then processing them in a separate loop.

    Parameters:
    -----------
    soup : BeautifulSoup
        The parsed HTML content to clean.
    
    tag_list : list or str
        A list of tag names (e.g., ['span', 'a']) or a space-separated string (e.g., 'span a') specifying
        which tags should be checked and unwrapped if redundant.

    Returns:
    --------
    None
        This function modifies the BeautifulSoup object in place, unwrapping redundant tags as needed.

    Example:
    --------
    >>> from bs4 import BeautifulSoup
    >>> html_content = '''
    ... <p><span><span class="bold">Table of Contents</span></span></p>
    ... <p><a><span class="italic"><span class="underline">Title Page</span></span></a></p>
    ... '''
    >>> soup = BeautifulSoup(html_content, 'html.parser')
    >>> unwrap_redundant_tags(soup, 'span a')
    >>> print(soup)
    <p><span class="bold">Table of Contents</span></p>
    <p><span class="italic"><span class="underline">Title Page</span></span></p>

    Notes:
    ------
    - This function only unwraps tags that contain no attributes and have a single child with identical text content.
    - The function operates in place, meaning it directly modifies the `soup` object passed to it.
    """
    if isinstance(tag_list, str):
        tag_list = tag_list.split()

    # Step 1: Collect tags to unwrap
    tags_to_unwrap = []
    for tag in soup.descendants:
        if tag.name in tag_list:
            # Check if the tag has no attributes and exactly one child that is a tag
            if not tag.attrs and len(tag.contents) == 1 and isinstance(tag.contents[0], Tag):
                child = tag.contents[0]
                # If tag adds no unique structure or information, mark it for unwrapping
                if tag.get_text(strip=True) == child.get_text(strip=True):
                    tags_to_unwrap.append(tag)

    # Step 2: Unwrap collected tags
    for tag in tags_to_unwrap:
        tag.unwrap()


def remove_tag_whitespace(html_str: str) -> str:
    """
    Removes any whitespace between adjacent HTML tags in an HTML string. This function is 
    designed to clean up HTML content by minimizing unnecessary spacing between elements, 
    which can improve readability in structured processing.

    Args:
        html_str (str): The HTML string to be processed. Must be well-formed for accurate parsing.

    Returns:
        str: The cleaned HTML string with no whitespace between adjacent tags. Tags that 
             originally had whitespace between them will now be directly adjacent.
    
    Example:
        >>> html_str = "<body> <p>This is some text.</p>   <br> </body>"
        >>> remove_tag_whitespace(html_str)
        '<body><p>This is some text.</p><br></body>'
    
    Notes:
        - This function uses BeautifulSoup to parse the HTML and then removes whitespace between 
          tags using a regular expression.
        - The function assumes that `html_str` is a well-formed HTML string. Malformed HTML may 
          lead to unexpected behavior.
        - BeautifulSoup automatically corrects certain HTML issues, so the output may differ 
          slightly in structure if the input was not well-formed.
    
    Raises:
        ValueError: If the input is not a valid HTML string or is an empty string.
    
    """
    if not html_str.strip():
        raise ValueError("Input HTML string cannot be empty or whitespace-only.")

    # Use BeautifulSoup to parse and normalize the HTML structure
    soup = BeautifulSoup(html_str, 'html.parser')
    
    # Convert back to string, then use regex to remove whitespace between tags
    cleaned_html = re.sub(r'>\s+<', '><', str(soup))
    
    return cleaned_html

def normalize_quotes(text: str) -> str:
    """
    Transforms all smart quotes in the input text to standard straight quotes.
    
    This function replaces both single and double smart quotes (Unicode) with
    their standard straight quote counterparts. Specifically, it:
    
    - Converts left and right single smart quotes (‘ and ’) to ASCII single quote (').
    - Converts left and right double smart quotes (“ and ”) to ASCII double quote (").

    Parameters
    ----------
    text : str
        The input text containing potential smart quotes.
    
    Returns
    -------
    str
        The text with all smart quotes replaced by standard straight quotes.

    Examples
    --------
    >>> text = '“This is a ‘smart’ quoted text.”'
    >>> normalize_quotes(text)
    '"This is a \'smart\' quoted text."'

    Notes
    -----
    Smart quotes are often automatically inserted by word processors but can
    introduce inconsistencies when parsing or tokenizing text data. This function
    is useful for data preprocessing, ensuring uniform quote styles in text for
    tasks like NLP model training or XML/HTML parsing.

    """
    # Replace left and right double smart quotes with straight double quote
    text = text.replace("\u201C", "\"").replace("\u201D", "\"")
    # Replace left and right single smart quotes with straight single quote
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    return text