from tnh_scholar.prompt_system.config.policy import ValidationPolicy
from tnh_scholar.prompt_system.domain.models import Prompt, PromptMetadata, RenderParams
from tnh_scholar.prompt_system.service.validator import PromptValidator


def make_prompt(
    version: str = "1.0.0",
    template: str = "Hi",
    required: list[str] | None = None,
    metadata_extra: dict | None = None,
) -> Prompt:
    metadata_kwargs = {
        "key": "test",
        "name": "test",
        "version": version,
        "description": "desc",
        "role": "task",
        "task_type": "test",
        "required_variables": required or [],
        "output_contract": {"mode": "text"},
    }
    if metadata_extra:
        metadata_kwargs.update(metadata_extra)
    metadata = PromptMetadata(**metadata_kwargs)
    return Prompt(name="test", version=version, template=template, metadata=metadata)


def test_validate_accepts_numeric_major_version():
    validator = PromptValidator(ValidationPolicy())
    result = validator.validate(make_prompt(version="1"))
    assert result.valid


def test_validate_accepts_legacy_task_type_when_role_missing():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(metadata_extra={"role": None, "task_type": "planner"})

    result = validator.validate(prompt)

    assert result.valid


def test_validate_rejects_missing_role_and_unknown_task_type():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(metadata_extra={"role": None, "task_type": "unknown"})

    result = validator.validate(prompt)

    assert not result.valid
    assert any(err.code == "MISSING_ROLE" for err in result.errors)


def test_validate_rejects_invalid_version():
    validator = PromptValidator(ValidationPolicy())
    result = validator.validate(make_prompt(version="one"))
    assert not result.valid
    assert any(err.code == "INVALID_VERSION" for err in result.errors)


def test_validate_rejects_strict_input_without_required_true():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(
        metadata_extra={
            "inputs": [
                {
                    "name": "harness_report",
                    "required": False,
                    "strictness": "strict",
                }
            ]
        }
    )

    result = validator.validate(prompt)

    assert not result.valid
    assert any(err.code == "INVALID_INPUT_STRICTNESS" for err in result.errors)


def test_validate_allows_loose_input_without_required_true():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(
        metadata_extra={
            "inputs": [
                {
                    "name": "context_notes",
                    "required": False,
                    "strictness": "loose",
                }
            ]
        }
    )

    result = validator.validate(prompt)

    assert result.valid
    assert not any(err.code == "INVALID_INPUT_STRICTNESS" for err in result.errors)


def test_validate_rejects_json_output_without_schema_ref():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(
        metadata_extra={
            "output_contract": {
                "mode": "json",
            }
        }
    )

    result = validator.validate(prompt)

    assert not result.valid
    assert any(err.code == "MISSING_SCHEMA_REF" for err in result.errors)


def test_validate_rejects_artifacts_output_without_artifact_declarations():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(
        metadata_extra={
            "output_contract": {
                "mode": "artifacts",
            }
        }
    )

    result = validator.validate(prompt)

    assert not result.valid
    assert any(err.code == "MISSING_ARTIFACTS" for err in result.errors)


def test_validate_rejects_missing_required_fields():
    validator = PromptValidator(ValidationPolicy())
    metadata = PromptMetadata(
        key="",
        name="",
        version="",
        description="desc",
        role=None,
        task_type="unknown",
        output_contract={"mode": "text"},
    )
    prompt = Prompt(name="test", version="1", template="", metadata=metadata)

    result = validator.validate(prompt)

    assert not result.valid
    assert any(err.code == "MISSING_NAME" for err in result.errors)
    assert any(err.code == "MISSING_VERSION" for err in result.errors)
    assert any(err.code == "MISSING_ROLE" for err in result.errors)
    assert any(err.code == "MISSING_TEMPLATE" for err in result.errors)
    assert any(err.code == "MISSING_KEY" for err in result.errors)


def test_validate_rejects_invalid_template_syntax():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(template="Hello {{ name }")

    result = validator.validate(prompt)

    assert not result.valid
    assert any(err.code == "INVALID_TEMPLATE" for err in result.errors)


def test_validate_rejects_missing_output_contract_when_model_is_mutated():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt()
    prompt.metadata = prompt.metadata.model_copy(update={"output_contract": None})

    result = validator.validate(prompt)

    assert not result.valid
    assert any(err.code == "MISSING_OUTPUT_CONTRACT" for err in result.errors)


def test_validate_render_reports_missing_required_vars():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(required=["name"])
    params = RenderParams(variables={})

    result = validator.validate_render(prompt, params)

    assert not result.valid
    assert any(err.code == "MISSING_REQUIRED_VARS" for err in result.errors)


def test_validate_render_reports_missing_required_strict_input():
    validator = PromptValidator(ValidationPolicy())
    prompt = make_prompt(
        metadata_extra={
            "inputs": [
                {
                    "name": "harness_report",
                    "required": True,
                    "strictness": "strict",
                }
            ]
        }
    )
    params = RenderParams(variables={})

    result = validator.validate_render(prompt, params)

    assert not result.valid
    assert any(err.code == "MISSING_REQUIRED_VARS" for err in result.errors)


def test_validate_render_allows_extra_when_policy_allows_extra_variables():
    validator = PromptValidator(
        ValidationPolicy(mode="strict", allow_extra_variables=True)
    )
    prompt = make_prompt(required=["name"])
    params = RenderParams(variables={"name": "x", "extra": "allowed"})

    result = validator.validate_render(prompt, params)

    assert result.valid
    assert not any(err.code == "EXTRA_VARIABLES" for err in result.errors)


def test_validate_render_allows_extra_when_policy_warns():
    validator = PromptValidator(
        ValidationPolicy(mode="warn", allow_extra_variables=False)
    )
    prompt = make_prompt(required=["name"])
    params = RenderParams(variables={"name": "x", "extra": "y"})

    result = validator.validate_render(prompt, params)

    assert result.valid
    assert any(w.code == "EXTRA_VARIABLES" for w in result.warnings)


def test_validate_render_allows_input_text_even_when_strict():
    validator = PromptValidator(ValidationPolicy(mode="strict"))
    prompt = make_prompt(required=["name"])
    params = RenderParams(variables={"name": "x", "input_text": "from file"})

    result = validator.validate_render(prompt, params)

    assert result.valid
    assert not any(err.code == "EXTRA_VARIABLES" for err in result.errors)


def test_validate_render_rejects_other_extra_variables_when_input_text_allowed():
    validator = PromptValidator(ValidationPolicy(mode="strict"))
    prompt = make_prompt(required=["name"])
    params = RenderParams(variables={"name": "x", "input_text": "ok", "extra": "nope"})

    result = validator.validate_render(prompt, params)

    assert not result.valid
    extras = [err for err in result.errors if err.code == "EXTRA_VARIABLES"]
    assert len(extras) == 1
    assert "extra" in extras[0].message
    assert "input_text" not in extras[0].message
