"""Tests for token counting utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from tnh_scholar.gen_ai_service.models.domain import Message
from tnh_scholar.gen_ai_service.utils.token_utils import (
    estimate_max_completion_tokens,
    token_count,
    token_count_file,
    token_count_messages,
)


def test_token_count_simple():
    """Test basic token counting."""
    # Simple greeting
    count = token_count("Hello, world!")
    assert count > 0
    assert token_count("Hello, world! Hello!") >= count  # Longer text >= shorter text

    # Empty string
    assert token_count("") == 0

    # Longer text
    text = "This is a longer piece of text that should have more tokens."
    count = token_count(text)
    assert count > 10


def test_token_count_different_models():
    """Test token counting across different models.

    Note: If tiktoken encoding is unavailable (offline/network issues),
    the function falls back to character count. In that case, counts
    will equal text length rather than proper token counts.
    """
    text = "Hello, world!"

    count_gpt4 = token_count(text, model="gpt-4o")
    count_gpt35 = token_count(text, model="gpt-3.5-turbo")

    # Both counts should be positive
    assert count_gpt4 > 0
    assert count_gpt35 > 0

    # Counts should be similar (same encoding for modern models)
    # Allow larger tolerance to handle fallback encoding case
    assert abs(count_gpt4 - count_gpt35) <= len(text)


def test_token_count_file(tmp_path: Path):
    """Test counting tokens in a file."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_content = "This is a test file with some content.\nIt has multiple lines."
    test_file.write_text(test_content)

    # Count tokens
    count = token_count_file(test_file)

    # Should match direct count
    direct_count = token_count(test_content)
    assert count == direct_count

    # Should be positive
    assert count > 0


def test_token_count_file_not_found():
    """Test token counting with non-existent file."""
    with pytest.raises(FileNotFoundError):
        token_count_file(Path("/nonexistent/file.txt"))


def test_token_count_messages_empty():
    """Test token counting with empty message list."""
    assert token_count_messages([]) == 0


def test_token_count_messages_single():
    """Test token counting with single message."""
    messages = [
        Message(role="user", content="Hello!")
    ]

    count = token_count_messages(messages)

    # Should include at least the content tokens
    assert count >= token_count("Hello!")


def test_token_count_messages_conversation():
    """Test token counting with multi-message conversation."""
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="What is Python?"),
        Message(role="assistant", content="Python is a programming language."),
    ]

    count = token_count_messages(messages)

    # Should exceed combined raw content tokens due to overhead
    combined_content = "".join(m.content for m in messages if isinstance(m.content, str))
    assert count >= token_count(combined_content)


def test_token_count_messages_with_content_parts():
    """Ensure structured content parts are flattened safely."""
    messages = [
        Message(
            role="user",
            content=[
                {"type": "text", "text": "Please describe this image."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.png",
                        "detail": "low",
                    },
                },
            ],
        )
    ]

    count = token_count_messages(messages)

    assert count > 10
    assert isinstance(count, int)


def test_estimate_max_completion_tokens():
    """Test estimating max completion tokens."""
    # Small prompt with large context window
    max_tokens = estimate_max_completion_tokens(
        prompt_tokens=1000,
        model="gpt-4o"
    )

    # Should leave plenty of room (128k context - 1k prompt - buffer)
    assert max_tokens > 120_000
    assert max_tokens < 128_000


def test_estimate_max_completion_tokens_near_limit():
    """Test estimation when prompt is near context limit."""
    # Prompt near limit
    with pytest.raises(ValueError, match="exceeds or nearly exceeds"):
        estimate_max_completion_tokens(
            prompt_tokens=8000,
            model="gpt-4",  # 8k context
            context_limit=8192
        )


def test_estimate_max_completion_tokens_custom_limit():
    """Test estimation with custom context limit."""
    max_tokens = estimate_max_completion_tokens(
        prompt_tokens=1000,
        context_limit=10_000
    )

    # Should respect custom limit
    assert max_tokens > 8_000  # 10k - 1k - buffer
    assert max_tokens < 9_000


def test_estimate_max_completion_tokens_gpt5_family():
    """GPT-5 variants should resolve to the configured context window."""
    max_tokens = estimate_max_completion_tokens(
        prompt_tokens=1_000,
        model="gpt-5-mini",
    )

    assert max_tokens > 150_000
    assert max_tokens < 200_000


def test_estimate_max_completion_tokens_with_negative_prompt_tokens():
    """Negative prompts should raise early."""
    with pytest.raises(ValueError, match="prompt_tokens must be non-negative"):
        estimate_max_completion_tokens(prompt_tokens=-1)
