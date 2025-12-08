import pytest

from tnh_scholar.prompt_system.config.policy import PromptRenderPolicy
from tnh_scholar.prompt_system.domain.models import Prompt, PromptMetadata, RenderParams
from tnh_scholar.prompt_system.service.renderer import PromptRenderer


def make_prompt(template: str, required: list[str] | None = None, metadata_extra: dict | None = None) -> Prompt:
    metadata = PromptMetadata(
        key="test",
        name="test",
        version="1.0.0",
        description="desc",
        task_type="test",
        required_variables=required or [],
        **(metadata_extra or {}),
    )
    return Prompt(name="test", version="1.0.0", template=template, metadata=metadata)


def test_render_applies_variable_precedence():
    policy = PromptRenderPolicy(precedence_order=["settings_defaults", "caller_context"])
    renderer = PromptRenderer(policy, settings_defaults={"name": "default"})
    prompt = make_prompt("Hello {{ name }}!")

    params = RenderParams(variables={"name": "caller"})
    rendered = renderer.render(prompt, params)

    assert rendered.system.strip() == "Hello caller!"


def test_render_raises_on_invalid_template():
    renderer = PromptRenderer(PromptRenderPolicy())
    prompt = make_prompt("Hello {{ name }")  # missing brace

    with pytest.raises(ValueError):
        renderer.render(prompt, RenderParams(variables={"name": "x"}))


def test_render_includes_user_input_as_message():
    renderer = PromptRenderer(PromptRenderPolicy())
    prompt = make_prompt("Hello {{ name }}!")

    rendered = renderer.render(
        prompt, RenderParams(variables={"name": "caller"}, user_input="hi there")
    )

    assert len(rendered.messages) == 1
    assert rendered.messages[0].content == "hi there"
