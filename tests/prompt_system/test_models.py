from tnh_scholar.prompt_system.domain.models import (
    PromptValidationResult,
    RenderParams,
    ValidationIssue,
)


def test_validation_result_succeeded_with_no_errors():
    result = PromptValidationResult(valid=True)
    assert result.succeeded()


def test_validation_result_fails_when_errors_present():
    result = PromptValidationResult(
        valid=True,
        errors=[
            ValidationIssue(level="error", code="TEST", message="issue"),
        ],
    )
    assert not result.succeeded()


def test_render_params_defaults_are_empty():
    params = RenderParams()
    assert params.variables == {}
    assert params.user_input is None
