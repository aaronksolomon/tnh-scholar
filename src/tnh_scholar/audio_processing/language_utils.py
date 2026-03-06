from __future__ import annotations


def normalize_language_code(language: str | None) -> str | None:
    """Normalize common language labels to compact language codes."""
    if language is None:
        return None
    cleaned = language.strip().lower()
    if not cleaned:
        return None
    primary_tag = cleaned.replace("_", "-").split("-", maxsplit=1)[0]
    if len(primary_tag) == 2:
        return primary_tag
    match cleaned:
        case "english":
            return "en"
        case "vietnamese":
            return "vi"
        case "chinese" | "mandarin" | "cantonese":
            return "zh"
        case "japanese":
            return "ja"
        case "korean":
            return "ko"
        case _:
            return cleaned
