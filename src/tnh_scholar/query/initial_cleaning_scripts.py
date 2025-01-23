import spacy
from bs4 import BeautifulSoup
from ebooklib import epub


def extract_content(soup):
    """
    Extracts content from a BeautifulSoup object considering blockquotes, spans, and paragraphs.
    """
    chapter_title = None

    # Look for blockquote or span elements that might contain the chapter title
    possible_titles = soup.find_all(["blockquote", "span"])
    for title in possible_titles:
        text = title.get_text().strip()
        if "Chapter" in text:  # Basic check for chapter titles
            chapter_title = text
            break  # Stop after finding the first relevant title

    # Collect paragraphs and blockquote content
    paragraphs = []
    for para in soup.find_all(["p", "blockquote"]):
        text = para.get_text().strip()
        if text:  # Only add non-empty text
            paragraphs.append(text)

    return chapter_title, paragraphs


def extract_text_and_metadata(file_path):
    """
    Extracts text, chapter titles, and metadata (like book title and author) from an EPUB file.

    Args:
        file_path (str): The path to the EPUB file to be processed.

    Returns:
        dict: A dictionary with metadata (title, author) and a list of chapter texts.
    """
    # Read the EPUB file
    book = epub.read_epub(file_path)
    content_with_metadata = {"metadata": {}, "chapters": []}

    # Extract metadata (title and author)
    metadata = book.get_metadata("DC", "title")
    if metadata:
        content_with_metadata["metadata"]["title"] = metadata[0][0]

    author = book.get_metadata("DC", "creator")
    if author:
        content_with_metadata["metadata"]["author"] = author[0][0]

    # Get items of the desired media type (HTML content)
    for item in book.get_items_of_media_type("application/xhtml+xml"):
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(item.get_body_content(), "html.parser")

        chapter_title, chapter_content = extract_content(soup)
        content_with_metadata["chapters"].append(
            {"chapter": chapter_title, "content": chapter_content}
        )

    return content_with_metadata


# Load SpaCy for sentence parsing
nlp = spacy.load("en_core_web_sm")


def clean_and_tag_text(content_with_metadata):
    cleaned_data = []

    for item in content_with_metadata:
        doc = nlp(item["text"])
        sentences = [sent.text.strip() for sent in doc.sents]

        # Store cleaned text alongside metadata
        cleaned_data.append(
            {
                "chapter": item["chapter"],
                "sentences": sentences,
                # Add page number here if available
                "page_number": item.get("page_number", None),
            }
        )
    return cleaned_data
