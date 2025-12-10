from __future__ import annotations

import pytest

from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams, apply_policy
from tnh_scholar.gen_ai_service.config.settings import Settings
from tnh_scholar.gen_ai_service.models.domain import CompletionResult, Message, RenderedPrompt, Role
from tnh_scholar.gen_ai_service.models.errors import SafetyBlocked
from tnh_scholar.gen_ai_service.routing.model_router import select_provider_and_model
from tnh_scholar.gen_ai_service.safety import safety_gate
from tnh_scholar.gen_ai_service.safety.safety_gate import SafetyReport
from tnh_scholar.prompt_system.domain.models import PromptMetadata


def _prompt_metadata(
    *,
    default_model: str | None = None,
    output_mode: str | None = None,
) -> PromptMetadata:
    return PromptMetadata(
        key="k",
        name="n",
        version="1.0.0",
        description="desc",
        task_type="task",
        required_variables=[],
        default_variables={},
        tags=[],
        default_model=default_model,
        output_mode=output_mode,
    )


def test_apply_policy_precedence_prefers_call_hint_over_prompt_default():
    settings = Settings(_env_file=None, default_model="gpt-settings")
    metadata = _prompt_metadata(default_model="gpt-meta", output_mode="json")

    resolved = apply_policy(
        intent="translate",
        call_hint="gpt-call",
        prompt_metadata=metadata,
        settings=settings,
    )

    assert resolved.model == "gpt-call"
    assert resolved.output_mode == "json"
    assert resolved.provider == settings.default_provider


def test_apply_policy_falls_back_to_settings_defaults_when_no_metadata():
    settings = Settings(_env_file=None, default_model="gpt-settings")

    resolved = apply_policy(
        intent=None,
        call_hint=None,
        prompt_metadata=None,
        settings=settings,
    )

    assert resolved.model == "gpt-settings"
    assert resolved.output_mode == "text"
    assert "unspecified" in (resolved.routing_reason or "")


def test_apply_policy_routing_reason_includes_intent_and_hints():
    settings = Settings(_env_file=None, default_model="gpt-settings")
    metadata = _prompt_metadata(default_model="gpt-meta", output_mode="json")

    resolved = apply_policy(
        intent="translate",
        call_hint="gpt-call",
        prompt_metadata=metadata,
        settings=settings,
    )

    reason = resolved.routing_reason or ""
    assert "intent=translate" in reason
    assert "call_hint=yes" in reason
    assert "prompt_default=yes" in reason


def test_apply_policy_uses_prompt_default_when_no_call_hint():
    settings = Settings(_env_file=None, default_model="gpt-settings")
    metadata = _prompt_metadata(default_model="gpt-meta", output_mode="text")

    resolved = apply_policy(
        intent=None,
        call_hint=None,
        prompt_metadata=metadata,
        settings=settings,
    )

    assert resolved.model == "gpt-meta"
    assert resolved.output_mode == "text"


def test_router_switches_to_structured_capable_model_for_json_mode():
    settings = Settings(_env_file=None, default_model="gpt-4o-mini")
    params = ResolvedParams(
        provider="openai",
        model="gpt-3.5-turbo",
        temperature=0.5,
        max_output_tokens=128,
        output_mode="json",
    )

    routed = select_provider_and_model(
        intent=None,
        params=params,
        settings=settings,
    )

    assert routed.model != "gpt-3.5-turbo"
    assert routed.output_mode == "json"
    assert "router" in (routed.routing_reason or "")


def test_router_keeps_structured_capable_model_for_json_mode():
    settings = Settings(_env_file=None, default_model="gpt-4o-mini")
    params = ResolvedParams(
        provider="openai",
        model="gpt-4o-mini",
        temperature=0.5,
        max_output_tokens=128,
        output_mode="json",
    )

    routed = select_provider_and_model(
        intent="summarize",
        params=params,
        settings=settings,
    )

    assert routed.model == "gpt-4o-mini"
    assert "intent=summarize" in (routed.routing_reason or "")


def test_router_leaves_model_for_text_mode():
    settings = Settings(_env_file=None, default_model="gpt-4o-mini")
    params = ResolvedParams(
        provider="openai",
        model="gpt-3.5-turbo",
        temperature=0.5,
        max_output_tokens=128,
        output_mode="text",
    )

    routed = select_provider_and_model(
        intent=None,
        params=params,
        settings=settings,
    )

    assert routed.model == "gpt-3.5-turbo"
    assert "router" not in (routed.routing_reason or "")


def test_safety_gate_blocks_on_character_limit():
    settings = Settings(_env_file=None, max_input_chars=16)
    selection = ResolvedParams(
        provider=settings.default_provider,
        model=settings.default_model,
        temperature=0.2,
        max_output_tokens=50,
    )

    rendered = RenderedPrompt(
        system="system text",
        messages=[Message(role=Role.user, content="user content longer than limit")],
    )

    with pytest.raises(SafetyBlocked, match="Prompt too large"):
        safety_gate.pre_check(rendered, selection, settings)


def test_safety_gate_blocks_on_context_window_overflow():
    settings = Settings(_env_file=None)
    selection = ResolvedParams(
        provider=settings.default_provider,
        model="gpt-3.5-turbo",
        temperature=0.2,
        max_output_tokens=200_000,  # exceeds any known context window
    )

    rendered = RenderedPrompt(
        system="system text",
        messages=[Message(role=Role.user, content="small text")],
    )

    with pytest.raises(SafetyBlocked, match="Context window exceeded"):
        safety_gate.pre_check(rendered, selection, settings)


def test_safety_gate_blocks_on_budget_overflow():
    settings = Settings(_env_file=None, max_dollars=0.0001)
    selection = ResolvedParams(
        provider=settings.default_provider,
        model=settings.default_model,
        temperature=0.2,
        max_output_tokens=10_000,
    )

    rendered = RenderedPrompt(
        system="system text",
        messages=[Message(role=Role.user, content="budget heavy")],
    )

    with pytest.raises(SafetyBlocked, match="budget"):
        safety_gate.pre_check(rendered, selection, settings)


def test_safety_gate_warnings_for_metadata_and_non_string_content():
    settings = Settings(_env_file=None, max_input_chars=2000, max_dollars=10.0)
    selection = ResolvedParams(
        provider=settings.default_provider,
        model=settings.default_model,
        temperature=0.2,
        max_output_tokens=50,
    )

    rendered = RenderedPrompt(
        system="ok",
        messages=[
            Message.model_construct(role=Role.user, content=[{"type": "text", "text": "coerce me"}]),
        ],
    )

    metadata = _prompt_metadata(default_model=None, output_mode=None)
    metadata.safety_level = "sensitive"

    report = safety_gate.pre_check(rendered, selection, settings, prompt_metadata=metadata)
    warnings = report.warnings
    assert any("coerced" in w for w in warnings or [""])
    assert any("sensitive" in w for w in warnings)


def test_safety_gate_returns_report_and_warnings(monkeypatch: pytest.MonkeyPatch):
    settings = Settings(_env_file=None, max_input_chars=2000, max_dollars=10.0)
    selection = ResolvedParams(
        provider=settings.default_provider,
        model=settings.default_model,
        temperature=0.2,
        max_output_tokens=50,
    )

    rendered = RenderedPrompt(
        system="ok",
        messages=[Message(role=Role.user, content="content")],
    )

    report = safety_gate.pre_check(rendered, selection, settings)
    assert isinstance(report, SafetyReport)
    assert report.prompt_tokens >= 0
    assert report.context_limit > 0
    assert report.estimated_cost >= 0


def test_safety_gate_post_check_returns_empty_for_none():
    assert safety_gate.post_check(None) == []


def test_safety_gate_post_check_warns_on_empty_result():
    result = CompletionResult(
        text="",
        usage=None,
        model="gpt-test",
        provider="openai",
    )
    warnings = safety_gate.post_check(result)
    assert "empty-result" in warnings
