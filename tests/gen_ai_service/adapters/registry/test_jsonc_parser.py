"""Tests for JSONC parser behavior."""

import pytest

from tnh_scholar.gen_ai_service.adapters.registry.jsonc_parser import JsoncParser


def test_parse_string_preserves_comment_tokens_inside_strings() -> None:
    parser = JsoncParser()
    content = """{
      "url": "https://example.com/path//not-a-comment",
      "pattern": "/* not a comment */"
    }"""

    data = parser.parse_string(content)

    assert data["url"].endswith("//not-a-comment")
    assert data["pattern"] == "/* not a comment */"


def test_parse_string_raises_on_unterminated_block_comment() -> None:
    parser = JsoncParser()
    content = """{
      "name": "value",
      /* missing end
      "other": "value"
    }"""

    with pytest.raises(ValueError, match="Unterminated block comment"):
        parser.parse_string(content)


def test_parse_string_strips_trailing_commas_outside_strings() -> None:
    parser = JsoncParser()
    content = """{
      "name": "value,}",
      "items": [
        "a",
        "b",
      ],
      "nested": {
        "x": 1,
      },
    }"""

    data = parser.parse_string(content)

    assert data["name"] == "value,}"
    assert data["items"] == ["a", "b"]
    assert data["nested"]["x"] == 1
