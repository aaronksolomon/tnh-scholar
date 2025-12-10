from __future__ import annotations

import pytest

from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams, apply_policy
from tnh_scholar.gen_ai_service.config.settings import Settings
from tnh_scholar.gen_ai_service.models.domain import Message, RenderedPrompt, Role
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
