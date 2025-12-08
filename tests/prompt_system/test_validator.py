from tnh_scholar.prompt_system.config.policy import ValidationPolicy
from tnh_scholar.prompt_system.domain.models import Prompt, PromptMetadata, RenderParams
from tnh_scholar.prompt_system.service.validator import PromptValidator


def make_prompt(version: str = "1.0.0", template: str = "Hi", required=None) -> Prompt:
    metadata = PromptMetadata(
        key="test",
        name="test",
        version=version,
        description="desc",
        task_type="test",
        required_variables=required or [],
    )
    return Prompt(name="test", version=version, template=template, metadata=metadata)


def test_validate_rejects_invalid_version():
    validator = PromptValidator(ValidationPolicy())
    result = validator.validate(make_prompt(version="1"))
    assert not result.valid
    assert any(err.code == "INVALID_VERSION" for err in result.errors)


def test_validate_render_reports_missing_required_vars():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(required=["name"])
    params = RenderParams(variables={})

    result = validator.validate_render(prompt, params)

    assert not result.valid
    assert any(err.code == "MISSING_REQUIRED_VARS" for err in result.errors)


def test_validate_render_allows_extra_when_policy_warns():
    validator = PromptValidator(
        ValidationPolicy(mode="warn", allow_extra_variables=False)
    )
    prompt = make_prompt(required=["name"])
    params = RenderParams(variables={"name": "x", "extra": "y"})

    result = validator.validate_render(prompt, params)

    assert result.valid
    assert any(w.code == "EXTRA_VARIABLES" for w in result.warnings)
