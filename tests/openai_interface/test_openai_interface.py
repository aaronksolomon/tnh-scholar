import os
import pytest
from dotenv import load_dotenv
from openai import OpenAI
from tnh_scholar.openai_interface.openai_interface import OpenAIClient

# Set dummy API key for testing
os.environ["OPENAI_API_KEY"] = "test_api_key"


@pytest.mark.parametrize(
    "test_id, expected_client_type",
    [
        ("valid_api_key_provided", OpenAI),
        ("api_key_with_trailing_spaces", OpenAI),  # Edge case: Trailing spaces
        ("api_key_with_leading_spaces", OpenAI),  # Edge case: Leading spaces
    ],
)
def test_get_instance_happy_path(test_id, expected_client_type, monkeypatch):
    # Arrange
    if test_id == "api_key_with_trailing_spaces":
        monkeypatch.setattr(os, "getenv", lambda x: "test_api_key   ")
    elif test_id == "api_key_with_leading_spaces":
        monkeypatch.setattr(os, "getenv", lambda x: "   test_api_key")

    # Act
    client = OpenAIClient.get_instance()

    # Assert
    assert isinstance(client, expected_client_type)


@pytest.mark.parametrize(
    "test_id, env_var_value, expected_error",
    [
        ("missing_api_key", None, ValueError),
        ("empty_api_key", "", ValueError),
        ("api_key_with_only_spaces", "   ", ValueError),  # Edge case
    ],
)
def test_get_instance_missing_api_key(test_id, env_var_value, expected_error, monkeypatch):
    # Arrange
    monkeypatch.setattr(os, "getenv", lambda x: env_var_value)

    # Act & Assert
    with pytest.raises(expected_error):
        OpenAIClient.get_instance()


def test_get_instance_singleton(monkeypatch):
    # Arrange
    monkeypatch.setattr(os, "getenv", lambda x: "test_api_key")

    # Act
    client1 = OpenAIClient.get_instance()
    client2 = OpenAIClient.get_instance()

    # Assert
    assert client1 is client2


def test_init():
    # Arrange
    api_key = "test_api_key"

    # Act
    client = OpenAIClient(api_key=api_key)

    # Assert
    assert isinstance(client.client, OpenAI)

import pytest
from tnh_scholar.openai_interface.openai_interface import generate_messages


@pytest.mark.parametrize(
    "test_id, system_message, data_list, expected_length",
    [
        (
            "single_data_element",
            "Test system message",
            [{"key": "value"}],
            1,
        ),
        (
            "multiple_data_elements",
            "Test system message",
            [{"key1": "value1"}, {"key2": "value2"}],
            2,
        ),
        ("no_data_elements", "Test system message", [], 0),  # Edge case: empty list
        ("empty_system_message", "", [{"key": "value"}], 1),  # Edge case
    ],
)
def test_generate_messages_happy_path(test_id, system_message, data_list, expected_length):
    # Arrange
    def user_message_wrapper(data):
        return str(data)

    # Act
    messages = generate_messages(system_message, user_message_wrapper, data_list)

    # Assert
    assert len(messages) == expected_length
    if messages:
        assert messages[0][0]["role"] == "system"
        assert messages[0][0]["content"] == system_message
        assert messages[0][1]["role"] == "user"
        assert messages[0][1]["content"] == str(data_list[0])


@pytest.mark.parametrize(
    "test_id, system_message, data_list, wrapper_side_effect, expected_error",
    [
        (
            "wrapper_raises_exception",
            "Test system message",
            [{"key": "value"}],
            TypeError,
            TypeError,
        ),
    ],
)
def test_generate_messages_wrapper_exception(
    test_id, system_message, data_list, wrapper_side_effect, expected_error
):
    # Arrange
    def user_message_wrapper(data):
        raise wrapper_side_effect

    # Act & Assert
    with pytest.raises(expected_error):
        generate_messages(system_message, user_message_wrapper, data_list)

import pytest
from unittest.mock import Mock, patch
from tnh_scholar.openai_interface.openai_interface import run_immediate_chat_process, OPEN_AI_DEFAULT_MODEL

# Dummy data for model settings
open_ai_model_settings = {
    OPEN_AI_DEFAULT_MODEL: {"max_tokens": 100},
    "another_model": {"max_tokens": 50},
}

@pytest.mark.parametrize(
    "test_id, messages, max_tokens, response_format, model, expected_model_call",
    [
        (
            "default_model_no_response_format",
            [{"role": "user", "content": "test"}],
            0,
            None,
            OPEN_AI_DEFAULT_MODEL,
            "create",
        ),
        (
            "default_model_with_response_format",
            [{"role": "user", "content": "test"}],
            50,
            {"type": "json_object"},
            OPEN_AI_DEFAULT_MODEL,
            "parse",
        ),
        (
            "different_model_no_response_format",
            [{"role": "user", "content": "test"}],
            0,
            None,
            "another_model",
            "create",
        ),
        (
            "different_model_with_response_format",
            [{"role": "user", "content": "test"}],
            25,
            {"type": "json_object"},
            "another_model",
            "parse",
        ),
        (
            "max_tokens_specified",  # Edge case: max_tokens specified
            [{"role": "user", "content": "test"}],
            75,
            None,
            OPEN_AI_DEFAULT_MODEL,
            "create",
        ),

    ],
)
def test_run_immediate_chat_process_happy_path(
    test_id, messages, max_tokens, response_format, model, expected_model_call, monkeypatch
):
    # Arrange
    mock_client = Mock()
    mock_create = mock_client.chat.completions.create
    mock_parse = mock_client.beta.chat.completions.parse
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_api_client", lambda: mock_client)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.open_ai_model_settings", open_ai_model_settings)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())


    # Act
    run_immediate_chat_process(messages, max_tokens, response_format, model)

    # Assert
    if expected_model_call == "create":
        mock_create.assert_called_once_with(
            messages=messages, model=model, max_completion_tokens=max_tokens if max_tokens != 0 else open_ai_model_settings[model]['max_tokens']
        )
        mock_parse.assert_not_called()
    else:
        mock_parse.assert_called_once_with(
            messages=messages, model=model, response_format=response_format, max_completion_tokens=max_tokens
        )
        mock_create.assert_not_called()


@pytest.mark.parametrize(
    "test_id, messages, max_tokens, model, expected_error",
    [
        (
            "max_tokens_exceeded",
            [{"role": "user", "content": "test"}],
            150,
            OPEN_AI_DEFAULT_MODEL,
            ValueError,
        ),
        (
            "max_tokens_exceeded_different_model",
            [{"role": "user", "content": "test"}],
            75,
            "another_model",
            ValueError,
        ),
    ],
)
def test_run_immediate_chat_process_max_tokens_exceeded(
    test_id, messages, max_tokens, model, expected_error, monkeypatch
):
    # Arrange
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_api_client", Mock())
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.open_ai_model_settings", open_ai_model_settings)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())

    # Act & Assert
    with pytest.raises(expected_error):
        run_immediate_chat_process(messages, max_tokens, model=model)


@pytest.mark.parametrize(
    "test_id, messages, max_tokens, model, api_exception",
    [
        (
            "api_exception",
            [{"role": "user", "content": "test"}],
            50,
            OPEN_AI_DEFAULT_MODEL,
            Exception("API Error"),
        ),
    ],
)
def test_run_immediate_chat_process_api_exception(
    test_id, messages, max_tokens, model, api_exception, monkeypatch
):
    # Arrange
    mock_client = Mock()
    mock_create = mock_client.chat.completions.create
    mock_create.side_effect = api_exception
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_api_client", lambda: mock_client)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.open_ai_model_settings", open_ai_model_settings)
    mock_logger = Mock()
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", mock_logger)

    # Act
    result = run_immediate_chat_process(messages, max_tokens, model=model)

    # Assert
    assert result is None
    mock_logger.error.assert_called_once()

import pytest
import time
from unittest.mock import Mock, patch
from tnh_scholar.openai_interface.openai_interface import poll_batch_for_response


@pytest.mark.parametrize(
    "test_id, batch_status_responses, expected_result",
    [
        ("completed_immediately", ["completed"], ["test_response"]),
        ("completed_after_two_attempts", ["processing", "completed"], ["test_response"]),
        (
            "completed_after_two_attempts_with_backoff",
            ["processing", "completed"],
            ["test_response"],
        ),
    ],
)
def test_poll_batch_for_response_success(test_id, batch_status_responses, expected_result, monkeypatch):
    # Arrange
    mock_get_batch_status = Mock(side_effect=batch_status_responses)
    mock_get_batch_response = Mock(return_value=["test_response"])
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_batch_status", mock_get_batch_status)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_batch_response", mock_get_batch_response)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())
    batch_id = "test_batch_id"

    # Act
    result = poll_batch_for_response(batch_id, interval=0.1, timeout=1, backoff_factor=1)  # Shorten intervals for testing

    # Assert
    assert result == expected_result


@pytest.mark.parametrize(
    "test_id, batch_status_responses, expected_result",
    [
        ("failed_immediately", ["failed"], False),
        ("failed_after_two_attempts", ["processing", "failed"], False),
        ("timeout", ["processing", "processing", "processing"], False),  # Simulate timeout
        ("invalid_status", ["invalid_status"], False),  # Simulate invalid status
        ("empty_status", [""], False),  # Simulate empty status
        ("none_status", [None], False),  # Simulate None status
    ],
)
def test_poll_batch_for_response_failure(test_id, batch_status_responses, expected_result, monkeypatch):
    # Arrange
    mock_get_batch_status = Mock(side_effect=batch_status_responses)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_batch_status", mock_get_batch_status)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())
    batch_id = "test_batch_id"

    # Act
    if test_id == "timeout":
        result = poll_batch_for_response(batch_id, interval=0.1, timeout=0.1)
    else:
        result = poll_batch_for_response(batch_id, interval=0.1, timeout=1)

    # Assert
    assert result == expected_result


def test_poll_batch_for_response_get_batch_response_exception(monkeypatch):
    # Arrange
    mock_get_batch_status = Mock(return_value="completed")
    mock_get_batch_response = Mock(side_effect=Exception("Test Exception"))
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_batch_status", mock_get_batch_status)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_batch_response", mock_get_batch_response)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())
    batch_id = "test_batch_id"

    # Act & Assert
    with pytest.raises(RuntimeError):
        poll_batch_for_response(batch_id, interval=0.1, timeout=1)

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from tnh_scholar.openai_interface.openai_interface import start_batch


@pytest.mark.parametrize(
    "test_id, jsonl_file_content, description",
    [
        ("no_description", '{"messages": []}\n', ""),
        ("with_description", '{"messages": []}\n', "test description"),
    ],
)
def test_start_batch_happy_path(test_id, jsonl_file_content, description, tmp_path, monkeypatch):
    # Arrange
    jsonl_file = tmp_path / "test.jsonl"
    jsonl_file.write_text(jsonl_file_content)
    mock_client = Mock()
    mock_file_create = mock_client.files.create.return_value
    mock_file_create.id = "test_file_id"
    mock_batch_create = mock_client.batches.create.return_value
    mock_batch_create.id = "test_batch_id"

    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_api_client", lambda: mock_client)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface._log_batch_start_info", Mock())

    # Act
    batch = start_batch(jsonl_file, description)

    # Assert
    assert isinstance(batch, Mock)
    assert batch.id == "test_batch_id"
    mock_client.files.create.assert_called_once()
    mock_client.batches.create.assert_called_once()


@pytest.mark.parametrize(
    "test_id, jsonl_file, description, expected_error",
    [
        ("wrong_type", "test.jsonl", "", TypeError),
        ("file_not_found", Path("non_existent_file.jsonl"), "", FileNotFoundError),
    ],
)
def test_start_batch_exceptions(test_id, jsonl_file, description, expected_error, tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_api_client", Mock())

    # Act & Assert
    with pytest.raises(expected_error):
        start_batch(jsonl_file, description)


@pytest.mark.parametrize(
    "test_id, side_effect, expected_return",
    [
        ("file_upload_failed", Exception("File upload error"), {"error": "File upload failed: File upload error"}),
        ("batch_creation_failed", Exception("Batch creation error"), {"error": "Batch creation failed: Batch creation error"}),
    ],
)
def test_start_batch_api_errors(test_id, side_effect, expected_return, tmp_path, monkeypatch):
    # Arrange
    jsonl_file = tmp_path / "test.jsonl"
    jsonl_file.write_text('{"messages": []}\n')
    mock_client = Mock()
    if test_id == "file_upload_failed":
        mock_client.files.create.side_effect = side_effect
    elif test_id == "batch_creation_failed":
        mock_client.batches.create.side_effect = side_effect
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.get_api_client", lambda: mock_client)

    # Act
    result = start_batch(jsonl_file)

    # Assert
    assert result == expected_return
    
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import time
from tnh_scholar.openai_interface.openai_interface import (
    start_batch_with_retries,
    DEFAULT_MAX_BATCH_RETRY,
)


@pytest.mark.parametrize(
    "test_id, start_batch_responses, poll_batch_responses, expected_retries",
    [
        ("success_on_first_try", [{"id": "batch_id"}], [["response"]], 0),
        ("success_on_second_try", [{"error": "Error"}, {"id": "batch_id"}], [[], ["response"]], 1),
        ("success_on_third_try", [{"error": "Error"}, {"error": "Error"}, {"id": "batch_id"}], [[], [], ["response"]], 2),
    ],
)
def test_start_batch_with_retries_success(test_id, start_batch_responses, poll_batch_responses, expected_retries, tmp_path, monkeypatch):
    # Arrange
    jsonl_file = tmp_path / "test.jsonl"
    jsonl_file.write_text('{"messages": []}\n')
    mock_start_batch = Mock(side_effect=start_batch_responses)
    mock_poll_batch = Mock(side_effect=poll_batch_responses)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.start_batch", mock_start_batch)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.poll_batch_for_response", mock_poll_batch)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())

    # Act
    response = start_batch_with_retries(jsonl_file, retry_delay=0.1, poll_interval=0.1, timeout=1)

    # Assert
    assert response == ["response"]
    assert mock_start_batch.call_count == expected_retries + 1
    assert mock_poll_batch.call_count == expected_retries + 1


@pytest.mark.parametrize(
    "test_id, start_batch_responses, poll_batch_responses",
    [
        ("all_retries_fail", [{"error": "Error"}] * DEFAULT_MAX_BATCH_RETRY, [False] * DEFAULT_MAX_BATCH_RETRY),
        ("start_batch_always_fails", [{"error": "Error"}] * DEFAULT_MAX_BATCH_RETRY, []),
        ("poll_batch_always_fails", [{"id": "batch_id"}] * DEFAULT_MAX_BATCH_RETRY, [False] * DEFAULT_MAX_BATCH_RETRY),
        ("start_batch_returns_none", [None] * DEFAULT_MAX_BATCH_RETRY, []),
        ("start_batch_returns_dict_without_id", [{}] * DEFAULT_MAX_BATCH_RETRY, []),

    ],
)
def test_start_batch_with_retries_failure(test_id, start_batch_responses, poll_batch_responses, tmp_path, monkeypatch):
    # Arrange
    jsonl_file = tmp_path / "test.jsonl"
    jsonl_file.write_text('{"messages": []}\n')
    mock_start_batch = Mock(side_effect=start_batch_responses)
    mock_poll_batch = Mock(side_effect=poll_batch_responses if poll_batch_responses else [])

    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.start_batch", mock_start_batch)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.poll_batch_for_response", mock_poll_batch)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())

    # Act & Assert
    with pytest.raises(RuntimeError):
        start_batch_with_retries(jsonl_file, retry_delay=0.1, poll_interval=0.1, timeout=1)

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from tnh_scholar.openai_interface.openai_interface import run_single_batch


@pytest.mark.parametrize(
    "test_id, user_prompts, max_token_list, expected_response",
    [
        ("single_prompt", ["prompt1"], [100], ["response1"]),
        ("multiple_prompts", ["prompt1", "prompt2"], [100, 200], ["response1", "response2"]),
        ("no_prompts", [], [], []),  # Edge case: empty prompts
        ("no_max_tokens", ["prompt1"], [], ["response1"]),  # Edge case: empty max_token_list
    ],
)
def test_run_single_batch_happy_path(test_id, user_prompts, max_token_list, expected_response, monkeypatch):
    # Arrange
    mock_generate_messages = Mock(return_value=[{"messages": [{"content": p}]} for p in user_prompts])
    mock_create_jsonl = Mock()
    mock_start_batch = Mock(return_value=expected_response)

    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.generate_messages", mock_generate_messages)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.create_jsonl_file_for_batch", mock_create_jsonl)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.start_batch_with_retries", mock_start_batch)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())

    # Act
    response = run_single_batch(user_prompts, "system message", max_token_list=max_token_list)

    # Assert
    assert response == expected_response
    mock_generate_messages.assert_called_once()
    mock_create_jsonl.assert_called_once()
    mock_start_batch.assert_called_once()


@pytest.mark.parametrize(
    "test_id, side_effect, expected_error",
    [
        ("generate_messages_fails", Exception("Test Exception"), Exception),
        ("create_jsonl_fails", Exception("Test Exception"), Exception),
        ("start_batch_fails", Exception("Test Exception"), Exception),
    ],
)
def test_run_single_batch_exceptions(test_id, side_effect, expected_error, monkeypatch):
    # Arrange
    user_prompts = ["prompt1"]
    mock_generate_messages = Mock(side_effect=side_effect if test_id == "generate_messages_fails" else [{"messages": [{"content": "prompt1"}]}])
    mock_create_jsonl = Mock(side_effect=side_effect if test_id == "create_jsonl_fails" else None)
    mock_start_batch = Mock(side_effect=side_effect if test_id == "start_batch_fails" else ["response1"])

    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.generate_messages", mock_generate_messages)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.create_jsonl_file_for_batch", mock_create_jsonl)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.start_batch_with_retries", mock_start_batch)
    monkeypatch.setattr("tnh_scholar.openai_interface.openai_interface.logger", Mock())

    # Act & Assert
    with pytest.raises(expected_error):
        run_single_batch(user_prompts, "system message")



