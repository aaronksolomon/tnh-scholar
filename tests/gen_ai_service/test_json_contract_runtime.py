from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from tnh_scholar.configuration.context import TNHContext
from tnh_scholar.gen_ai_service import service as service_module
from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams
from tnh_scholar.gen_ai_service.config.settings import GenAISettings
from tnh_scholar.gen_ai_service.models.domain import FailureReason, RenderRequest
from tnh_scholar.gen_ai_service.models.transport import (
    FinishReason,
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
    ProviderUsage,
    TextPayload,
)
from tnh_scholar.gen_ai_service.service import GenAIService
from tnh_scholar.prompt_system.service.contract_schema import PromptContractSchemaResolver


class DummyOpenAIClient:
    def __init__(self, api_key: str | None, organization: str | None):
        self.requests: list[ProviderRequest] = []
        self.response: ProviderResponse | None = None
        self.sdk_version = "openai-sdk-test"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        if self.response is None:
            raise AssertionError("test must set DummyOpenAIClient.response")
        return self.response


def _write_json_prompt(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("json-echo.md").write_text(
        dedent(
            """\
            ---
            key: json-echo
            name: json-echo
            version: 1.0.0
            description: JSON contract prompt for testing.
            role: task
            required_variables: []
            output_contract:
              mode: json
              schema_ref: tnh.testing.echo.v1
            ---
            Return a JSON object.
            """
        ),
        encoding="utf-8",
    )
    return prompt_dir


def _provider_response(text: str) -> ProviderResponse:
    return ProviderResponse(
        provider="openai",
        model="gpt-5-mini",
        status=ProviderStatus.OK,
        attempts=1,
        payload=TextPayload(text=text, finish_reason=FinishReason.STOP),
        usage=ProviderUsage(tokens_in=5, tokens_out=4, tokens_total=9),
    )


def _fake_apply_policy(intent, call_hint, **_):
    return ResolvedParams(
        provider="openai",
        model="gpt-5-mini",
        temperature=0.2,
        max_output_tokens=256,
        output_mode="json",
        seed=1,
        routing_reason="test-policy",
    )


def _fake_select(intent, params, settings, **_):
    return params


def test_gen_ai_service_validates_json_contract_and_canonicalizes_text(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    prompt_dir = _write_json_prompt(tmp_path)
    monkeypatch.setattr(service_module, "apply_policy", _fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", _fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setenv("TNH_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    dummy_client.response = _provider_response('{\n  "message": "hello"\n}')

    envelope = service.generate(
        RenderRequest(
            instruction_key="json-echo",
            user_input="ignored",
            variables={},
        )
    )

    assert envelope.outcome.value == "succeeded"
    response_format = dummy_client.requests[0].response_format
    assert response_format is not None
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "tnh_testing_echo_v1"
    assert response_format["json_schema"]["strict"] is False
    assert response_format["json_schema"]["schema"]["type"] == "object"
    assert envelope.result is not None
    assert envelope.result.json_value == {"message": "hello"}
    assert envelope.result.schema_ref == "tnh.testing.echo.v1"
    assert envelope.result.text == '{"message":"hello"}'


def test_gen_ai_service_maps_schema_validation_failures_to_failed_outcome(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    prompt_dir = _write_json_prompt(tmp_path)
    monkeypatch.setattr(service_module, "apply_policy", _fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", _fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setenv("TNH_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    dummy_client.response = _provider_response('{"message": 1}')

    envelope = service.generate(
        RenderRequest(
            instruction_key="json-echo",
            user_input="ignored",
            variables={},
        )
    )

    assert envelope.outcome.value == "failed"
    assert envelope.result is None
    assert envelope.failure is not None
    assert envelope.failure.reason == FailureReason.CONTRACT_VALIDATION_FAILED
    assert "schema 'tnh.testing.echo.v1'" in envelope.failure.message


def test_gen_ai_service_maps_malformed_json_to_failed_outcome(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    prompt_dir = _write_json_prompt(tmp_path)
    monkeypatch.setattr(service_module, "apply_policy", _fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", _fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setenv("TNH_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    dummy_client.response = _provider_response("{not-json")

    envelope = service.generate(
        RenderRequest(
            instruction_key="json-echo",
            user_input="ignored",
            variables={},
        )
    )

    assert envelope.outcome.value == "failed"
    assert envelope.result is None
    assert envelope.failure is not None
    assert envelope.failure.reason == FailureReason.CONTRACT_VALIDATION_FAILED
    assert "not valid JSON" in envelope.failure.message


def test_gen_ai_service_skips_openai_response_format_for_non_object_json_schema(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    prompt_dir = _write_json_prompt(tmp_path)
    builtin_root = tmp_path / "builtin"
    schema_dir = builtin_root / "schemas" / "prompt-contracts" / "tnh" / "testing" / "echo"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.joinpath("v1.schema.json").write_text(
        dedent(
            """\
            {
              "$schema": "https://json-schema.org/draft/2020-12/schema",
              "oneOf": [
                { "type": "object" },
                { "type": "array" }
              ]
            }
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(service_module, "apply_policy", _fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", _fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setattr(
        PromptContractSchemaResolver,
        "for_prompt_directory",
        classmethod(
            lambda cls, _prompts_base: cls(
                TNHContext(
                    builtin_root=builtin_root,
                    workspace_root=prompt_dir.parent,
                    user_root=tmp_path / "user",
                    correlation_id="corr",
                    session_id="sess",
                )
            )
        ),
    )
    monkeypatch.setenv("TNH_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    dummy_client.response = _provider_response('{"message":"hello"}')

    envelope = service.generate(
        RenderRequest(
            instruction_key="json-echo",
            user_input="ignored",
            variables={},
        )
    )

    assert envelope.outcome.value == "succeeded"
    assert dummy_client.requests[0].response_format is None


def test_gen_ai_service_sanitizes_openai_response_format_for_object_schema_with_top_level_anyof(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    prompt_dir = _write_json_prompt(tmp_path)
    builtin_root = tmp_path / "builtin"
    schema_dir = builtin_root / "schemas" / "prompt-contracts" / "tnh" / "testing" / "echo"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.joinpath("v1.schema.json").write_text(
        dedent(
            """\
            {
              "$schema": "https://json-schema.org/draft/2020-12/schema",
              "type": "object",
              "anyOf": [
                { "required": ["message"] },
                { "required": ["summary"] }
              ],
              "properties": {
                "message": { "type": "string" },
                "summary": { "type": "string" }
              }
            }
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(service_module, "apply_policy", _fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", _fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setattr(
        PromptContractSchemaResolver,
        "for_prompt_directory",
        classmethod(
            lambda cls, _prompts_base: cls(
                TNHContext(
                    builtin_root=builtin_root,
                    workspace_root=prompt_dir.parent,
                    user_root=tmp_path / "user",
                    correlation_id="corr",
                    session_id="sess",
                )
            )
        ),
    )
    monkeypatch.setenv("TNH_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    dummy_client.response = _provider_response('{"message":"hello"}')

    envelope = service.generate(
        RenderRequest(
            instruction_key="json-echo",
            user_input="ignored",
            variables={},
        )
    )

    assert envelope.outcome.value == "succeeded"
    response_format = dummy_client.requests[0].response_format
    assert response_format is not None
    assert response_format["type"] == "json_schema"
    schema = response_format["json_schema"]["schema"]
    assert schema["type"] == "object"
    assert "anyOf" not in schema


def test_openai_compatible_json_schema_strips_nested_unsupported_keywords() -> None:
    schema = {
        "type": "object",
        "properties": {
            "key_concepts": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string", "enum": ["a", "b"]}},
                ]
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "anyOf": [{"required": ["title"]}, {"required": ["title_en"]}],
                    "properties": {"title": {"type": "string"}},
                },
            },
        },
    }

    sanitized = service_module._openai_compatible_json_schema(schema)

    def assert_no_unsupported_keywords(node: object) -> None:
        if isinstance(node, dict):
            for keyword in ("oneOf", "anyOf", "allOf", "enum", "not"):
                assert keyword not in node
            for value in node.values():
                assert_no_unsupported_keywords(value)
            return
        if isinstance(node, list):
            for item in node:
                assert_no_unsupported_keywords(item)

    assert_no_unsupported_keywords(sanitized)


def test_sectioning_schema_requires_end_line_for_walkthrough_handoff() -> None:
    schemas_root = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "tnh_scholar"
        / "runtime_assets"
        / "schemas"
        / "prompt-contracts"
        / "tnh"
        / "sectioning"
    )

    for schema_name in ("default_section", "section_by_break"):
        schema_path = schemas_root / schema_name / "v1.schema.json"
        schema = service_module.json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False
        required_fields = schema["properties"]["sections"]["items"]["required"]
        assert schema["properties"]["sections"]["items"]["additionalProperties"] is False
        assert "end_line" in required_fields


def test_sectioning_schema_rejects_top_level_schema_echo_keys() -> None:
    schemas_root = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "tnh_scholar"
        / "runtime_assets"
        / "schemas"
        / "prompt-contracts"
        / "tnh"
        / "sectioning"
    )

    for schema_name in ("default_section", "section_by_break", "generate_sections_multi_lang"):
        schema_path = schemas_root / schema_name / "v1.schema.json"
        schema = service_module.json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False


def test_gen_ai_service_rejects_schema_echo_properties_wrapper(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    prompt_dir = _write_json_prompt(tmp_path)
    builtin_root = tmp_path / "builtin"
    schema_dir = builtin_root / "schemas" / "prompt-contracts" / "tnh" / "testing" / "echo"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.joinpath("v1.schema.json").write_text(
        dedent(
            """\
            {
              "$schema": "https://json-schema.org/draft/2020-12/schema",
              "type": "object",
              "required": ["document_summary", "sections"],
              "properties": {
                "document_summary": { "type": "string" },
                "sections": {
                  "type": "array",
                  "items": { "type": "object" }
                }
              }
            }
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(service_module, "apply_policy", _fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", _fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setattr(
        PromptContractSchemaResolver,
        "for_prompt_directory",
        classmethod(
            lambda cls, _prompts_base: cls(
                TNHContext(
                    builtin_root=builtin_root,
                    workspace_root=prompt_dir.parent,
                    user_root=tmp_path / "user",
                    correlation_id="corr",
                    session_id="sess",
                )
            )
        ),
    )
    monkeypatch.setenv("TNH_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    dummy_client.response = _provider_response(
        '{"type":"object","properties":{"document_summary":"summary","sections":[{"title":"One"}]}}'
    )

    envelope = service.generate(
        RenderRequest(
            instruction_key="json-echo",
            user_input="ignored",
            variables={},
        )
    )

    assert envelope.outcome.value == "failed"
    assert envelope.result is None
    assert envelope.failure is not None
    assert envelope.failure.reason == FailureReason.CONTRACT_VALIDATION_FAILED
    assert "schema 'tnh.testing.echo.v1'" in envelope.failure.message
