# version 2 testing of clearning scripts

import spacy

# Load a pretrained model, e.g., for sentence and chapter recognition
nlp = spacy.load("en_core_web_sm")


def process_book(book_text):
    """
    Process text to extract chapters and paragraphs using spaCy NLP model.

    Args:
        book_text (str): Raw text of the book.

    Returns:
        list: A list of (chapter_title, chapter_content) tuples.
    """
    doc = nlp(book_text)
    chapters = []
    chapter_title = ""
    chapter_content = []

    for sent in doc.sents:
        if "chapter" in sent.text.lower():
            # Store previous chapter if any
            if chapter_title:
                chapters.append((chapter_title, " ".join(chapter_content)))
            chapter_title = sent.text.strip()
            chapter_content = []
        else:
            chapter_content.append(sent.text.strip())

    if chapter_title:
        chapters.append((chapter_title, " ".join(chapter_content)))

    return chapters


from transformers import pipeline

# Load a pre-trained BERT model for classification
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def classify_heading(text):
    """
    Classifies text as heading or not using a Hugging Face model.

    Args:
        text (str): The text to classify.

    Returns:
        bool: True if the text is classified as a heading, otherwise False.
    """
    # Define candidate labels for zero-shot classification
    candidate_labels = ["heading", "paragraph"]

    result = classifier(text, candidate_labels)
    return result["labels"][0] == "heading"
