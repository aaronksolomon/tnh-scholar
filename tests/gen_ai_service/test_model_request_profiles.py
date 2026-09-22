"""Regression coverage for data-driven model compatibility and Astra requests."""

import json
from pathlib import Path

import httpx
import pytest
from openai import OpenAI
from pydantic import ValidationError

from tnh_scholar.cli_tools.tnh_gen.errors import ExitCode, map_exception
from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.gen_ai_service.config.registry import RegistryLoader, RegistryPaths
from tnh_scholar.gen_ai_service.models.domain import Message
from tnh_scholar.gen_ai_service.models.errors import ProviderError
from tnh_scholar.gen_ai_service.models.registry import ModelPricing
from tnh_scholar.gen_ai_service.models.request_profile import ModelRequestProfile
from tnh_scholar.gen_ai_service.models.transport import ProviderRequest
from tnh_scholar.gen_ai_service.providers import openai_adapter
from tnh_scholar.gen_ai_service.providers.openai_client import OpenAIClient
from tnh_scholar.gen_ai_service.safety import safety_gate


@pytest.fixture
def loader(monkeypatch: pytest.MonkeyPatch) -> RegistryLoader:
    builtins = Path(__file__).parents[2] / "src/tnh_scholar/runtime_assets/registries/providers"
    loader = RegistryLoader(registry_paths=RegistryPaths((builtins,), ()))
    monkeypatch.setattr(openai_adapter, "get_model_info", loader.get_model)
    return loader


def request(model: str, effort: str | None = None) -> ProviderRequest:
    return ProviderRequest(
        provider="openai",
        model=model,
        messages=[Message(role="user", content="Return ACK")],
        temperature=0.2,
        max_output_tokens=128,
        reasoning_effort=effort,
    )


@pytest.mark.parametrize("model", ["gpt-6-astra", "gpt-5.6", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"])
@pytest.mark.parametrize("effort", ["low", "medium", "high", "xhigh", "max"])
def test_model_efforts_reach_sdk_wire_unchanged(loader: RegistryLoader, model: str, effort: str) -> None:
    captured = []

    def respond(http_request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(http_request.content))
        return httpx.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 0,
                "model": model,
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": "ACK"}, "finish_reason": "stop"}
                ],
            },
        )

    client = OpenAIClient(api_key="test-key", organization=None)
    client._client.close()
    with OpenAI(api_key="test-key", http_client=httpx.Client(transport=httpx.MockTransport(respond))) as sdk:
        client._client = sdk
        client.generate(request(model, effort))
    assert captured[0]["reasoning_effort"] == effort
    assert "temperature" not in captured[0]
    assert captured[0]["max_completion_tokens"] == 128


@pytest.mark.parametrize("effort", ["none", "minimal", "maximum", "typo"])
def test_astra_rejects_unsupported_efforts(loader: RegistryLoader, effort: str) -> None:
    with pytest.raises(ValueError, match="Supported: low, medium, high, xhigh, max"):
        openai_adapter.OpenAIAdapter().to_openai_request(request("gpt-6-astra", effort))


@pytest.mark.parametrize("effort", [None, "auto"])
def test_astra_provider_default_omits_reasoning(loader: RegistryLoader, effort: str | None) -> None:
    mapped = openai_adapter.OpenAIAdapter().to_openai_request(request("gpt-6-astra", effort))
    assert mapped.reasoning_effort is None
    assert mapped.temperature is None


@pytest.mark.parametrize(
    "model,effort,expected,temperature",
    [
        ("gpt-5", None, "minimal", None),
        ("gpt-5-mini", None, "minimal", None),
        ("gpt-5.5", None, "high", None),
        ("gpt-5.5-latest", "xhigh", "xhigh", None),
        ("gpt-5.5", "auto", None, None),
        ("gpt-5.5", "none", "none", None),
        ("gpt-5.4", "high", "high", None),
        ("gpt-5.4", "none", "none", 0.2),
        ("gpt-5.4", "auto", None, 0.2),
        ("gpt-4o", None, None, 0.2),
    ],
)
def test_existing_models_and_aliases(
    loader: RegistryLoader,
    model: str,
    effort: str | None,
    expected: str | None,
    temperature: float | None,
) -> None:
    mapped = openai_adapter.OpenAIAdapter().to_openai_request(request(model, effort))
    assert mapped.reasoning_effort == expected
    assert mapped.temperature == temperature


def test_unknown_model_and_unsupported_reasoning_fail_explicitly(loader: RegistryLoader) -> None:
    adapter = openai_adapter.OpenAIAdapter()
    with pytest.raises(ConfigurationError, match="not found"):
        adapter.to_openai_request(request("gpt-future"))
    with pytest.raises(ValueError, match="Unsupported reasoning effort"):
        adapter.to_openai_request(request("gpt-4o", "high"))
    with pytest.raises(ValueError, match="Unsupported reasoning effort"):
        adapter.to_openai_request(request("gpt-5.5", "max"))


def test_new_model_and_effort_require_only_registry_data(
    loader: RegistryLoader,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = loader.get_provider("openai").model_dump(mode="json", by_alias=True)
    future = dict(registry["models"]["gpt-6-astra"])
    future["request_profile"] = {
        "reasoning_efforts": ["deep"],
        "default_reasoning_effort": "deep",
        "temperature": "never",
    }
    future["aliases"] = ["future-alias"]
    registry["models"]["future-model"] = future
    (tmp_path / "openai.jsonc").write_text(json.dumps(registry))
    custom = RegistryLoader(registry_paths=RegistryPaths((tmp_path,), ()))
    monkeypatch.setattr(openai_adapter, "get_model_info", custom.get_model)
    mapped = openai_adapter.OpenAIAdapter().to_openai_request(request("future-alias", "deep"))
    assert mapped.reasoning_effort == "deep"
    assert mapped.temperature is None


def test_user_override_replaces_request_profile(loader: RegistryLoader, tmp_path: Path) -> None:
    (tmp_path / "openai.jsonc").write_text(
        json.dumps(
            {
                "provider": "openai",
                "models": {
                    "gpt-6-astra": {
                        "request_profile": {
                            "reasoning_efforts": ["deep"],
                            "default_reasoning_effort": "deep",
                            "temperature": "never",
                        },
                        "pricing_tiers": {
                            "standard": {
                                "cache_write_input_per_1k": 0.02,
                                "long_context": {
                                    "input_token_threshold": 1000,
                                    "input_multiplier": 3,
                                    "output_multiplier": 2,
                                },
                            }
                        },
                    }
                },
            }
        )
    )
    custom = RegistryLoader(registry_paths=RegistryPaths(loader._paths.provider_dirs, (tmp_path,)))
    model = custom.get_model("openai", "gpt-6-astra")
    assert model.request_profile.resolve_reasoning(None, model="gpt-6-astra") == "deep"
    assert model.get_pricing().estimate_cost(2000, 1000) == pytest.approx(0.22)


@pytest.mark.parametrize(
    "payload",
    [
        {"reasoning_efforts": ["low"], "default_reasoning_effort": "max"},
        {"reasoning_efforts": ["auto"]},
        {"reasoning_efforts": ["high", "high"]},
        {"reasoning_efforts": [" HIGH "]},
        {"reasoning_eforts": ["high"]},
    ],
)
def test_invalid_registry_profile_fails_validation(payload: dict) -> None:
    with pytest.raises(ValidationError):
        ModelRequestProfile.model_validate(payload)


def test_astra_cost_handles_cache_writes_and_long_context(loader: RegistryLoader) -> None:
    pricing = loader.get_model("openai", "gpt-6-astra").get_pricing()
    assert pricing.estimate_cost(272_000, 1000) == pytest.approx(3.45)
    assert pricing.estimate_cost(272_001, 1000) == pytest.approx(6.875025)
    assert ModelPricing(input_per_1k=0.01, output_per_1k=0.05).estimate_cost(1000, 1000) == pytest.approx(
        0.06
    )


def test_registry_schema_accepts_bundled_profiles(loader: RegistryLoader) -> None:
    import jsonschema

    schema_path = loader._paths.provider_dirs[0] / "schema.json"
    # JSON serialization drops optional null fields that the hand-maintained schema omits.
    payload = loader.get_provider("openai").model_dump(mode="json", by_alias=True, exclude_none=True)
    jsonschema.validate(payload, json.loads(schema_path.read_text()))


@pytest.mark.parametrize("model,effort", [("gpt-4o", "high"), ("gpt-6-astra", "none")])
def test_client_preserves_unsupported_effort_as_input_error(
    loader: RegistryLoader,
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    effort: str,
) -> None:
    client = OpenAIClient(api_key="test-key", organization=None)

    def unexpected_dispatch(*args, **kwargs):
        pytest.fail("Invalid local request must never enter provider dispatch/retries")

    monkeypatch.setattr(client, "_call_with_retries", unexpected_dispatch)
    try:
        with pytest.raises(ValueError, match="Unsupported reasoning effort") as caught:
            client.generate(request(model, effort))
        assert map_exception(caught.value) == ExitCode.INPUT_ERROR
    finally:
        client._client.close()


def test_client_still_wraps_sdk_failures_as_provider_errors(
    loader: RegistryLoader,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = OpenAIClient(api_key="test-key", organization=None)
    failure = ValueError("SDK response parsing failed")

    def fail_in_sdk(*args, **kwargs):
        raise failure

    monkeypatch.setattr(client, "_chat_create", fail_in_sdk)
    try:
        with pytest.raises(ProviderError) as caught:
            client.generate(request("gpt-6-astra", "max"))
        assert caught.value.__cause__ is failure
        assert map_exception(caught.value) == ExitCode.PROVIDER_ERROR
    finally:
        client._client.close()


@pytest.mark.parametrize("tokens_in,expected", [(272_000, 3.45), (272_001, 6.875025)])
def test_cache_aware_estimate_preserves_astra_write_and_long_context_rates(
    loader: RegistryLoader,
    monkeypatch: pytest.MonkeyPatch,
    tokens_in: int,
    expected: float,
) -> None:
    monkeypatch.setattr(safety_gate, "get_registry_loader", lambda: loader)
    monkeypatch.setattr(safety_gate, "get_model_info", loader.get_model)
    cost = safety_gate._estimate_cost("openai", "gpt-6-astra", tokens_in, 1000, use_cache=True)
    assert cost == pytest.approx(expected)
    # Models without cache-write rates retain the existing cached-input discount.
    legacy = safety_gate._estimate_cost("openai", "gpt-5-mini", 1000, 1000, use_cache=True)
    assert legacy == pytest.approx(0.002025)


@pytest.mark.parametrize("model", ["gpt-5.6", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"])
@pytest.mark.parametrize("effort,expected", [(None, "medium"), ("auto", None), ("none", "none")])
def test_gpt56_default_and_disabled_reasoning(
    loader: RegistryLoader,
    model: str,
    effort: str | None,
    expected: str | None,
) -> None:
    info = loader.get_model("openai", model)
    assert info.context_window == 1_050_000
    assert info.max_output_tokens == 128_000
    mapped = openai_adapter.OpenAIAdapter().to_openai_request(request(model, effort))
    assert mapped.reasoning_effort == expected
    assert mapped.temperature is None


@pytest.mark.parametrize("model", ["gpt-5.6", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"])
@pytest.mark.parametrize("effort", ["minimal", "ultra", "typo"])
def test_gpt56_rejects_unsupported_reasoning(loader: RegistryLoader, model: str, effort: str) -> None:
    with pytest.raises(ValueError, match="Unsupported reasoning effort"):
        openai_adapter.OpenAIAdapter().to_openai_request(request(model, effort))


@pytest.mark.parametrize(
    "model,input_price,output_price",
    [
        ("gpt-5.6", 0.004, 0.020),
        ("gpt-5.6-sol", 0.004, 0.020),
        ("gpt-5.6-terra", 0.002, 0.012),
        ("gpt-5.6-luna", 0.0002, 0.0012),
    ],
)
def test_gpt56_pricing_surcharges(
    loader: RegistryLoader,
    model: str,
    input_price: float,
    output_price: float,
) -> None:
    pricing = loader.get_model("openai", model).get_pricing()
    assert pricing.input_per_1k == input_price
    assert pricing.output_per_1k == output_price
    assert pricing.estimate_cost(1000, 1000) == pytest.approx(input_price * 1.25 + output_price)
    assert pricing.estimate_cost(273000, 1000) == pytest.approx(
        input_price * 1.25 * 2 * 273 + output_price * 1.5
    )
