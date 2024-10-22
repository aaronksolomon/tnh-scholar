from bs4 import BeautifulSoup
from ebooklib import epub
import spacy

def extract_text_and_metadata(file_path):
    """
    Extracts text and associated metadata (chapter titles) from an EPUB file.
    
    This function reads an EPUB file, extracts the HTML content of each document within the book, and retrieves chapter titles (if available) and the associated paragraphs. The resulting content is returned as a list of dictionaries containing chapter titles and paragraph text.
    
    Args:
        file_path (str): The path to the EPUB file to be processed.
        
    Returns:
        list: A list of dictionaries, where each dictionary contains the following keys:
            - 'chapter': The chapter title (if available, otherwise None).
            - 'text': The paragraph text from the chapter.

    Example:
        >>> content = extract_text_and_metadata('book.epub')
        >>> print(content)
        [{'chapter': 'Chapter 1', 'text': 'This is the first paragraph of chapter 1.'},
         {'chapter': 'Chapter 1', 'text': 'This is the second paragraph of chapter 1.'},
         {'chapter': 'Chapter 2', 'text': 'This is the first paragraph of chapter 2.'}]
    """
    
    # Read the EPUB file
    book = epub.read_epub(file_path)
    content_with_metadata = []

    # Loop over all items in the EPUB file
    for item in book.get_items():
        # Only process document type items (EPUB documents)
        if item.get_type() == epub.EPUB_DOCUMENT:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            
            # Extract chapter titles (using 'h1' as the assumed chapter title tag)
            chapter_title = soup.find('h1').get_text() if soup.find('h1') else None
            # Extract paragraphs (using 'p' as the paragraph tag)
            paragraphs = soup.find_all('p')

            # Collect the text with metadata
            for para in paragraphs:
                content_with_metadata.append({
                    'chapter': chapter_title,
                    'text': para.get_text(),
                    # You can add logic for page number extraction if available
                })
    
    # Return the collected content
    return content_with_metadata

# Load SpaCy for sentence parsing
nlp = spacy.load("en_core_web_sm")

def clean_and_tag_text(content_with_metadata):
    cleaned_data = []
    
    for item in content_with_metadata:
        doc = nlp(item['text'])
        sentences = [sent.text.strip() for sent in doc.sents]

        # Store cleaned text alongside metadata
        cleaned_data.append({
            'chapter': item['chapter'],
            'sentences': sentences,
            # Add page number here if available
            'page_number': item.get('page_number', None)
        })
    return cleaned_data