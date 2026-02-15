from pathlib import Path

from tnh_scholar.prompt_system.mappers.prompt_mapper import PromptMapper


def test_to_file_request_strips_immutable_version_suffix():
    mapper = PromptMapper()
    base_path = Path("/tmp/prompts")

    resolved = mapper.to_file_request(
        "agent-orch/planner/evaluate_harness_report.v1",
        base_path,
    )

    assert resolved == base_path / "agent-orch/planner/evaluate_harness_report.md"


def test_to_key_from_path_supports_absolute_and_relative_paths(tmp_path: Path):
    mapper = PromptMapper()
    base_path = tmp_path / "prompts"
    absolute = base_path / "agent-orch" / "planner" / "evaluate.md"
    relative = Path("agent-orch/planner/evaluate.md")

    assert mapper.to_key_from_path(absolute, base_path) == "agent-orch/planner/evaluate"
    assert mapper.to_key_from_path(relative, base_path) == "agent-orch/planner/evaluate"


def test_to_key_from_path_keeps_absolute_path_when_not_under_base(tmp_path: Path):
    mapper = PromptMapper()
    base_path = tmp_path / "prompts"
    external_path = Path("/tmp/external/prompt.md")

    resolved = mapper.to_key_from_path(external_path, base_path)

    assert resolved.endswith("/tmp/external/prompt")


def test_to_domain_prompt_uses_source_key_when_frontmatter_key_missing():
    mapper = PromptMapper()
    content = """---
name: Planner Evaluate
version: 1
description: Evaluate planner output.
role: planner
output_contract:
  mode: text
---
Evaluate planner output.
"""

    prompt = mapper.to_domain_prompt(content, source_key="agent-orch/planner/evaluate")

    assert prompt.metadata.prompt_id == "agent-orch/planner/evaluate"
    assert prompt.metadata.key == "agent-orch/planner/evaluate"


def test_to_domain_prompt_canonicalizes_immutable_frontmatter_key():
    mapper = PromptMapper()
    content = """---
key: agent-orch/planner/evaluate.v1
name: Planner Evaluate
version: 1
description: Evaluate planner output.
role: planner
output_contract:
  mode: text
---
Evaluate planner output.
"""

    prompt = mapper.to_domain_prompt(content)

    assert prompt.metadata.canonical_key() == "agent-orch/planner/evaluate"


def test_to_domain_prompt_raises_when_frontmatter_missing():
    mapper = PromptMapper()

    try:
        mapper.to_domain_prompt("No frontmatter here.")
    except ValueError as exc:
        assert "missing or invalid YAML front matter" in str(exc)
    else:
        assert False, "Expected ValueError for missing frontmatter."


def test_to_domain_prompt_normalizes_legacy_variables_to_inputs():
    mapper = PromptMapper()
    content = """---
key: agent-orch/planner/evaluate
name: Planner Evaluate
version: 1
description: Evaluate planner output.
role: planner
required_variables:
  - harness_report
optional_variables:
  - context_notes
output_mode: text
---
Evaluate planner output.
"""

    prompt = mapper.to_domain_prompt(content)
    names_to_specs = {spec.name: spec for spec in prompt.metadata.inputs}

    assert names_to_specs["harness_report"].required
    assert names_to_specs["harness_report"].strictness.value == "strict"
    assert not names_to_specs["context_notes"].required
    assert names_to_specs["context_notes"].strictness.value == "loose"


def test_to_domain_prompt_normalizes_artifact_output_entries():
    mapper = PromptMapper()
    content = """---
key: agent-orch/harness/run_suite
name: Run Suite
version: 1
description: Execute generated harness.
role: eval
output_contract:
  mode: artifacts
  artifacts:
    - reports/harness_report.json
    - path: logs/stdout.txt
      required: true
---
Run the suite.
"""

    prompt = mapper.to_domain_prompt(content)
    contract = prompt.metadata.output_contract

    assert contract is not None
    assert contract.mode.value == "artifacts"
    assert len(contract.artifacts) == 2
    assert contract.artifacts[0].path == "reports/harness_report.json"
    assert not contract.artifacts[0].required
    assert contract.artifacts[1].path == "logs/stdout.txt"
    assert contract.artifacts[1].required


def test_to_domain_prompt_adds_warning_for_invalid_field_types():
    mapper = PromptMapper()
    content = """---
key: agent-orch/planner/evaluate
name: Planner Evaluate
version: 1
description: Evaluate planner output.
role: planner
required_variables: harness_report
default_variables: not-a-dict
output_mode: artifacts
warnings:
  - existing warning
---
Evaluate planner output.
"""

    prompt = mapper.to_domain_prompt(content)

    assert "existing warning" in prompt.metadata.warnings
    assert any(
        "required_variables" in warning for warning in prompt.metadata.warnings
    )
    assert any(
        "default_variables" in warning for warning in prompt.metadata.warnings
    )
    assert prompt.metadata.output_contract is not None
    assert prompt.metadata.output_contract.mode.value == "artifacts"


def test_to_domain_prompt_accepts_input_spec_list_and_legacy_json_mode():
    mapper = PromptMapper()
    content = """---
key: agent-orch/planner/evaluate
name: Planner Evaluate
version: 1
description: Evaluate planner output.
role: planner
inputs:
  - name: harness_report
    required: true
    strictness: strict
  - not-a-dict
output_mode: structured
---
Evaluate planner output.
"""

    prompt = mapper.to_domain_prompt(content)

    assert len(prompt.metadata.inputs) == 1
    assert prompt.metadata.inputs[0].name == "harness_report"
    assert prompt.metadata.output_contract is not None
    assert prompt.metadata.output_contract.mode.value == "json"


def test_to_domain_prompt_raises_when_key_and_source_are_missing():
    mapper = PromptMapper()
    content = """---
name: Planner Evaluate
version: 1
description: Evaluate planner output.
role: planner
output_contract:
  mode: text
---
Evaluate planner output.
"""

    try:
        mapper.to_domain_prompt(content)
    except ValueError as exc:
        assert "missing key/prompt_id and source key" in str(exc)
    else:
        assert False, "Expected ValueError when prompt key metadata is missing."
