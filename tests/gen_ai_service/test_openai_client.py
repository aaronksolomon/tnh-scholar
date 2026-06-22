from __future__ import annotations

from types import SimpleNamespace

from tnh_scholar.gen_ai_service.providers.openai_client import OpenAIClient


def test_openai_client_omits_temperature_for_legacy_gpt5_requests():
    client = OpenAIClient(api_key="test-key", organization=None)
    captured: dict[str, object] = {}

    def _create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace()

    client._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))
    request = SimpleNamespace(
        model="gpt-5",
        messages=[{"role": "user", "content": "Return ACK"}],
        temperature=None,
        max_completion_tokens=64,
        seed=None,
        reasoning_effort="minimal",
        response_format=None,
    )

    client._chat_create(request)

    assert "temperature" not in captured
    assert captured["reasoning_effort"] == "minimal"


def test_openai_client_keeps_temperature_for_gpt54_requests():
    client = OpenAIClient(api_key="test-key", organization=None)
    captured: dict[str, object] = {}

    def _create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace()

    client._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))
    request = SimpleNamespace(
        model="gpt-5.4",
        messages=[{"role": "user", "content": "Return ACK"}],
        temperature=0.2,
        max_completion_tokens=64,
        seed=None,
        reasoning_effort=None,
        response_format=None,
    )

    client._chat_create(request)

    assert captured["temperature"] == 0.2
    assert "reasoning_effort" not in captured


def test_openai_client_omits_max_completion_tokens_when_unset():
    client = OpenAIClient(api_key="test-key", organization=None)
    captured: dict[str, object] = {}

    def _create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace()

    client._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))
    request = SimpleNamespace(
        model="gpt-5.5",
        messages=[{"role": "user", "content": "Return ACK"}],
        temperature=None,
        max_completion_tokens=None,
        seed=None,
        reasoning_effort="high",
        response_format=None,
    )

    client._chat_create(request)

    assert "max_completion_tokens" not in captured
