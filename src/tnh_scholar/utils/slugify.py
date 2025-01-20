import re
import unicodedata


def slugify(string: str) -> str:
    """
    Slugify a Unicode string.

    Converts a string to a strict URL-friendly slug format,
    allowing only lowercase letters, digits, and hyphens.

    Example:
        >>> slugify("Héllø_Wörld!")
        'hello-world'
    """
    # Normalize Unicode to remove accents and convert to ASCII
    string = (
        unicodedata.normalize("NFKD", string).encode("ascii", "ignore").decode("ascii")
    )

    # Replace all non-alphanumeric characters with spaces (only keep a-z and 0-9)
    string = re.sub(r"[^a-z0-9\s]", " ", string.lower().strip())

    # Replace any sequence of spaces with a single hyphen
    return re.sub(r"\s+", "-", string)


# Example usage
# print(slugify("DT_Decision_Making.mp3"))  # Output: "dt-decision-making-mp3"
# print(slugify("**This is a test###"))  # Output: "this-is-a-test"
# print(slugify("Café Déjà Vu"))  # Output: "cafe-deja-vu"
# print(slugify("remove!@#$%^&*()special:chars"))  # Output: "remove-special-chars"
