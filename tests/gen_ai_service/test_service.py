from __future__ import annotations

from textwrap import dedent

import pytest

from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.gen_ai_service import service as service_module
from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams
from tnh_scholar.gen_ai_service.config.settings import GenAISettings
from tnh_scholar.gen_ai_service.infra.tracking.fingerprint import (
    hash_prompt_bytes,
    hash_user_string,
    hash_vars,
)
from tnh_scholar.gen_ai_service.models.domain import RenderRequest
from tnh_scholar.gen_ai_service.models.transport import (
    FinishReason,
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
    ProviderUsage,
    TextPayload,
)
from tnh_scholar.gen_ai_service.service import GenAIService


class DummyOpenAIClient:
    def __init__(self, api_key: str | None, organization: str | None):
        self.api_key = api_key
        self.organization = organization
        self.requests: list[ProviderRequest] = []
        self.response: ProviderResponse | None = None
        self.sdk_version = "openai-sdk-test"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        if self.response is None:
            raise AssertionError("test must set DummyOpenAIClient.response")
        return self.response


def _write_prompt(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("daily.md").write_text(
        dedent(
            """\
            ---
            key: daily
            name: daily
            version: 1.0.0
            description: Daily guidance prompt for testing.
            task_type: study-plan
            required_variables:
              - audience
            optional_variables:
              - location
            default_variables:
              location: Plum Village
            ---
            # Daily Guidance
            
            Offer help to {{ audience }} at {{ location }}.
            """
        )
    )
    return prompt_dir


def test_gen_ai_service_golden_path(tmp_path, monkeypatch: pytest.MonkeyPatch):
    prompt_dir = _write_prompt(tmp_path)

    policy_params = ResolvedParams(
        provider="openai",
        model="gpt-test-mini",
        temperature=0.55,
        max_output_tokens=256,
        seed=999,
    )

    apply_calls: list[tuple[str | None, str | None]] = []
    select_calls: list[tuple[str | None, ResolvedParams, GenAISettings]] = []

    def fake_apply_policy(intent, call_hint, **_):
        apply_calls.append((intent, call_hint))
        return policy_params

    def fake_select(intent, params, settings, **_):
        select_calls.append((intent, params, settings))
        return params

    monkeypatch.setattr(service_module, "apply_policy", fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setenv("TNH_PATTERN_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    assert service.settings.prompt_dir == prompt_dir

    provider_response = ProviderResponse(
        provider="openai",
        model=policy_params.model,
        status=ProviderStatus.OK,
        attempts=2,
        payload=TextPayload(text="Rendered completion", finish_reason=FinishReason.STOP),
        usage=ProviderUsage(tokens_in=123, tokens_out=45, tokens_total=168),
    )
    dummy_client.response = provider_response

    render_request = RenderRequest(
        instruction_key="daily",
        user_input="Where should I begin?",
        variables={"audience": "practitioners"},
        intent="study-plan",
    )

    envelope = service.generate(render_request)

    assert apply_calls == [("study-plan", None)]
    assert select_calls and select_calls[0][2] is settings

    assert len(dummy_client.requests) == 1
    provider_request = dummy_client.requests[0]
    assert provider_request.model == policy_params.model
    assert provider_request.temperature == policy_params.temperature
    assert provider_request.max_output_tokens == policy_params.max_output_tokens
    assert provider_request.seed == policy_params.seed
    assert provider_request.response_format is None
    assert provider_request.system == "# Daily Guidance\n\nOffer help to practitioners at Plum Village."
    assert provider_request.messages[0].content == render_request.user_input

    fingerprint = envelope.provenance.fingerprint
    prompt_bytes = prompt_dir.joinpath("daily.md").read_bytes()
    assert fingerprint.prompt_key == "daily"
    assert fingerprint.prompt_name == "daily"
    assert fingerprint.prompt_base_path == str(prompt_dir)
    assert fingerprint.prompt_content_hash == hash_prompt_bytes(prompt_bytes)
    assert fingerprint.variables_hash == hash_vars(render_request.variables or {})
    assert fingerprint.user_string_hash == hash_user_string(render_request.user_input)

    assert envelope.result is not None
    assert provider_response.payload is not None
    assert envelope.result.text == provider_response.payload.text
    assert envelope.result.usage and envelope.result.usage.total_tokens == 168
    assert envelope.provenance.provider == provider_response.provider
    assert envelope.provenance.model == provider_response.model
    assert envelope.provenance.attempt_count == provider_response.attempts


def test_missing_api_key_raises_configuration_error(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Test that GenAIService raises ConfigurationError when API key is missing."""
    prompt_dir = _write_prompt(tmp_path)

    monkeypatch.setenv("TNH_PATTERN_DIR", str(prompt_dir))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = GenAISettings(_env_file=None)

    with pytest.raises(ConfigurationError, match="Missing required API key: OPENAI_API_KEY"):
        GenAIService(settings=settings)
