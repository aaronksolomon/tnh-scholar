from tnh_scholar.prompt_system.domain.models import (
    PromptMetadata,
    PromptOutputContract,
    PromptOutputMode,
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
    assert not result.valid
    assert not result.succeeded()


def test_render_params_defaults_are_empty():
    params = RenderParams()
    assert params.variables == {}
    assert params.user_input is None


def test_prompt_metadata_coerces_integer_version_to_string():
    metadata = PromptMetadata(
        prompt_id="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version=1,
        description="desc",
        role="planner",
    )
    assert metadata.version == "1"


def test_prompt_metadata_sets_key_and_prompt_id_bidirectionally():
    from_key = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
    )
    from_prompt_id = PromptMetadata(
        prompt_id="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
    )

    assert from_key.prompt_id == "agent-orch/planner/evaluate"
    assert from_prompt_id.key == "agent-orch/planner/evaluate"


def test_prompt_metadata_maps_legacy_structured_to_json_contract():
    metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
        output_mode="structured",
    )
    assert metadata.output_contract is not None
    assert metadata.output_contract.mode == PromptOutputMode.json


def test_prompt_metadata_derives_role_from_legacy_task_type():
    metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        task_type="planner",
    )
    assert metadata.role == "planner"


def test_prompt_metadata_derives_task_type_from_role():
    metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
    )
    assert metadata.task_type == "planner"


def test_prompt_metadata_maps_output_contract_to_legacy_output_mode():
    metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
        output_contract=PromptOutputContract(mode=PromptOutputMode.artifacts),
    )
    assert metadata.output_mode == "artifacts"


def test_prompt_metadata_immutable_ref_uses_version_field():
    metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="2",
        description="desc",
        role="planner",
        output_contract=PromptOutputContract(mode=PromptOutputMode.text),
    )
    assert metadata.canonical_key() == "agent-orch/planner/evaluate"
    assert metadata.immutable_ref() == "agent-orch/planner/evaluate.v2"


def test_prompt_metadata_resolved_output_mode_prefers_contract_mode():
    metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
        output_contract=PromptOutputContract(mode=PromptOutputMode.artifacts),
    )
    assert metadata.resolved_output_mode() == PromptOutputMode.artifacts


def test_prompt_metadata_resolved_output_mode_falls_back_to_legacy_mode():
    metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
        output_mode="artifacts",
    )
    metadata = metadata.model_copy(update={"output_contract": None})

    assert metadata.resolved_output_mode() == PromptOutputMode.artifacts


def test_prompt_metadata_resolved_output_mode_falls_back_to_json_and_text():
    json_metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
        output_mode="json",
    ).model_copy(update={"output_contract": None})
    text_metadata = PromptMetadata(
        key="agent-orch/planner/evaluate",
        name="Planner Evaluate",
        version="1",
        description="desc",
        role="planner",
        output_mode="text",
    ).model_copy(update={"output_contract": None})

    assert json_metadata.resolved_output_mode() == PromptOutputMode.json
    assert text_metadata.resolved_output_mode() == PromptOutputMode.text
