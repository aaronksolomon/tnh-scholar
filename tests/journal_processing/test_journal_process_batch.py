from __future__ import annotations

import json
from pathlib import Path

from tnh_scholar.journal_processing import journal_process as jp


def test_generate_messages_builds_system_and_user_blocks():
    def wrap(value: str) -> str:
        return f"value={value}"

    messages = jp.generate_messages("system-msg", wrap, ["foo", "bar"])

    assert len(messages) == 2
    first = messages[0]
    assert first[0] == {"role": "system", "content": "system-msg"}
    assert first[1] == {"role": "user", "content": "value=foo"}
    second = messages[1]
    assert second[1]["content"] == "value=bar"


def test_create_jsonl_file_for_batch_writes_expected_payload(tmp_path):
    messages = [
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hello"},
        ]
    ]
    output = tmp_path / "requests.jsonl"

    written_path = jp.create_jsonl_file_for_batch(
        messages,
        output_file_path=output,
        max_token_list=[123],
        model="gpt-4o",
        json_mode=True,
    )

    assert written_path == output
    data = [json.loads(line) for line in output.read_text().splitlines() if line]
    assert len(data) == 1
    body = data[0]["body"]
    assert body["model"] == "gpt-4o"
    assert body["max_tokens"] == 123
    assert body["response_format"] == {"type": "json_object"}


def test_start_batch_with_retries_calls_simple_completion(monkeypatch, tmp_path):
    messages = [
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "first"},
        ],
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "second"},
        ],
    ]
    jsonl_path = jp.create_jsonl_file_for_batch(
        messages,
        output_file_path=tmp_path / "batch.jsonl",
        max_token_list=[10, 20],
    )

    calls: list[tuple[str, str, int]] = []

    def fake_simple_completion(*, system_message, user_message, model, max_tokens):
        calls.append((system_message, user_message, max_tokens))
        return f"{user_message}-resp"

    monkeypatch.setattr(jp, "simple_completion", fake_simple_completion)

    responses = jp.start_batch_with_retries(jsonl_path, description="unit-test")

    assert responses == ["first-resp", "second-resp"]
    assert calls == [("sys", "first", 10), ("sys", "second", 20)]


def test_run_immediate_chat_process_uses_simple_completion(monkeypatch):
    recorded = {}

    def fake_simple_completion(*, system_message, user_message, model, max_tokens):
        recorded["system"] = system_message
        recorded["user"] = user_message
        recorded["max_tokens"] = max_tokens
        recorded["model"] = model
        return "result"

    monkeypatch.setattr(jp, "simple_completion", fake_simple_completion)

    message = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "user text"},
    ]
    result = jp.run_immediate_chat_process(message, max_tokens=42, model="gpt-test")

    assert result == "result"
    assert recorded == {
        "system": "sys",
        "user": "user text",
        "max_tokens": 42,
        "model": "gpt-test",
    }
