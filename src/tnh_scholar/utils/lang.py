import pycountry
from langdetect import LangDetectException, detect

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)

def get_language_code_from_text(text: str) -> str:
    """
    Detect the language of the provided text using langdetect.

    Args:
        text: Text to analyze

                      code or 'name' for full English language name

    Returns:
        str: return result 'code' ISO 639-1 for detected language.

    Raises:
        ValueError: If text is empty or invalid
    """

    if not text or text.isspace():
        raise ValueError("Input text cannot be empty")

    sample = _get_sample_text(text)

    try:
        return detect(sample)
    except LangDetectException:
        logger.warning("Language could not be detected in get_language().")
        return "un"


def get_language_name_from_text(text: str) -> str:
    return get_language_from_code(get_language_code_from_text(text))


def get_language_from_code(code: str):
    if language := pycountry.languages.get(alpha_2=code):
        return language.name
    logger.warning(f"No language name found for code: {code}")
    return "Unknown"


def _get_sample_text(text: str, words_per_sample: int = 30) -> str:
    """
    Get text samples from beginning, 1/3 point, and 2/3 point.
    Each sample starts at nearest word boundary and contains ~N words.

    Args:
        text: Text to sample
        words_per_sample: Target number of words per sample
    """
    # For short texts, just return the original
    if len(text) < 1000:
        return text

    def get_words(start_idx: int) -> str:
        """Get approximately N words starting from index."""
        idx = start_idx
        word_count = 0

        # Skip initial whitespace
        while idx < len(text) and text[idx].isspace():
            idx += 1

        # Count words until we hit target
        pos = idx
        while pos < len(text) and word_count < words_per_sample:
            if text[pos].isspace():
                while pos < len(text) and text[pos].isspace():
                    pos += 1
                word_count += 1
            pos += 1

        return text[idx:pos]

    # Get samples from three positions
    third = len(text) // 3
    samples = [get_words(0), get_words(third), get_words(2 * third)]

    return " ... ".join(samples)
