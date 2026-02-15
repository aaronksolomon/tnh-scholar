import logging
from pathlib import Path

from tnh_scholar.prompt_system.adapters.filesystem_catalog_adapter import (
    FilesystemPromptCatalog,
)
from tnh_scholar.prompt_system.config.policy import ValidationPolicy
from tnh_scholar.prompt_system.config.prompt_catalog_config import PromptCatalogConfig
from tnh_scholar.prompt_system.mappers.prompt_mapper import PromptMapper
from tnh_scholar.prompt_system.service.loader import PromptLoader
from tnh_scholar.prompt_system.service.validator import PromptValidator


def write_prompt(tmp_path: Path, key: str, template: str = "Hello"):
    prompt_path = tmp_path / f"{key}.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    name = key.split("/")[-1]
    content = f"""---
key: {key}
name: {name}
version: 1.0.0
description: desc
task_type: test
required_variables: []
---
{template}
"""
    prompt_path.write_text(content, encoding="utf-8")


def test_filesystem_catalog_loads_prompt(tmp_path: Path):
    write_prompt(tmp_path, "sample", "Hi {{who}}")
    config = PromptCatalogConfig(repository_path=tmp_path)
    mapper = PromptMapper()
    validator = PromptValidator(ValidationPolicy())
    loader = PromptLoader(validator)
    catalog = FilesystemPromptCatalog(config, mapper=mapper, loader=loader)

    prompt = catalog.get("sample")

    assert prompt.metadata.name == "sample"
    assert "Hi" in prompt.template


def test_filesystem_catalog_returns_cached_prompt(tmp_path: Path):
    write_prompt(tmp_path, "cached", "First version")
    config = PromptCatalogConfig(repository_path=tmp_path, cache_ttl_s=60)
    mapper = PromptMapper()
    loader = PromptLoader(PromptValidator(ValidationPolicy()))
    catalog = FilesystemPromptCatalog(config, mapper=mapper, loader=loader)

    first = catalog.get("cached")

    # Overwrite file with invalid version; cache should still return first prompt
    write_prompt(tmp_path, "cached", "Second version with bad version")
    (tmp_path / "cached.md").write_text(
        """---
key: cached
name: cached
version: invalid
description: desc
task_type: test
required_variables: []
---
Second
""",
        encoding="utf-8",
    )

    second = catalog.get("cached")

    assert first.template == second.template


def test_filesystem_catalog_list_returns_namespaced_keys(tmp_path: Path):
    write_prompt(tmp_path, "agent-orch/planner/evaluate")
    write_prompt(tmp_path, "core/task/summarize")
    config = PromptCatalogConfig(repository_path=tmp_path)
    mapper = PromptMapper()
    loader = PromptLoader(PromptValidator(ValidationPolicy()))
    catalog = FilesystemPromptCatalog(config, mapper=mapper, loader=loader)

    keys = sorted(metadata.canonical_key() for metadata in catalog.list())

    assert keys == ["agent-orch/planner/evaluate", "core/task/summarize"]


def test_filesystem_catalog_get_accepts_immutable_reference(tmp_path: Path):
    write_prompt(tmp_path, "agent-orch/planner/evaluate", "Hi {{who}}")
    config = PromptCatalogConfig(repository_path=tmp_path)
    mapper = PromptMapper()
    loader = PromptLoader(PromptValidator(ValidationPolicy()))
    catalog = FilesystemPromptCatalog(config, mapper=mapper, loader=loader)

    prompt = catalog.get("agent-orch/planner/evaluate.v1")

    assert prompt.metadata.canonical_key() == "agent-orch/planner/evaluate"


def test_filesystem_catalog_falls_back_on_invalid_frontmatter(tmp_path: Path, caplog):
    caplog.set_level(logging.WARNING)
    (tmp_path / "legacy.md").write_text(
        ("---\n# invalid frontmatter body\n---\nLegacy body\n"),
        encoding="utf-8",
    )
    config = PromptCatalogConfig(repository_path=tmp_path)
    mapper = PromptMapper()
    loader = PromptLoader(PromptValidator(ValidationPolicy()))
    catalog = FilesystemPromptCatalog(config, mapper=mapper, loader=loader)

    prompt = catalog.get("legacy")

    assert prompt.metadata.version == "0.0.0-invalid"
    assert "legacy" in prompt.metadata.warnings[0]
    assert prompt.template == "Legacy body\n"
    assert any("Prompt 'legacy' warning" in message for message in caplog.messages)


def test_filesystem_catalog_falls_back_on_validation_errors(tmp_path: Path):
    (tmp_path / "bad-json.md").write_text(
        """---
key: bad-json
name: bad-json
version: 1
description: desc
role: planner
output_contract:
  mode: json
---
{{ result }}
""",
        encoding="utf-8",
    )
    config = PromptCatalogConfig(repository_path=tmp_path, validation_on_load=True)
    mapper = PromptMapper()
    loader = PromptLoader(PromptValidator(ValidationPolicy()))
    catalog = FilesystemPromptCatalog(config, mapper=mapper, loader=loader)

    prompt = catalog.get("bad-json")

    assert prompt.template.strip() == "{{ result }}"
    assert any("Invalid prompt" in warning for warning in prompt.metadata.warnings)


def test_filesystem_catalog_best_effort_body_without_frontmatter_block(tmp_path: Path):
    config = PromptCatalogConfig(repository_path=tmp_path)
    mapper = PromptMapper()
    loader = PromptLoader(PromptValidator(ValidationPolicy()))
    catalog = FilesystemPromptCatalog(config, mapper=mapper, loader=loader)

    body = catalog._best_effort_body("just plain body")

    assert body == "just plain body"


def test_filesystem_catalog_best_effort_body_uses_delimiter_fallback(
    tmp_path: Path, monkeypatch
):
    config = PromptCatalogConfig(repository_path=tmp_path)
    mapper = PromptMapper()
    loader = PromptLoader(PromptValidator(ValidationPolicy()))
    catalog = FilesystemPromptCatalog(config, mapper=mapper, loader=loader)

    from tnh_scholar.metadata import metadata as metadata_module

    def _raise_extract(_: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(metadata_module.Frontmatter, "extract", _raise_extract)

    body = catalog._best_effort_body("---\nnot-usable\n---\nRecovered body")

    assert body == "Recovered body"


def test_mapper_split_handles_bom_and_delimiters():
    mapper = PromptMapper()
    content = (
        "\ufeff---\n"
        "key: x\n"
        "name: x\n"
        "version: 1.0.0\n"
        "description: d\n"
        "task_type: t\n"
        "required_variables: []\n"
        "---\n"
        "Body"
    )
    metadata, body = mapper._split_frontmatter(content)
    assert metadata["name"] == "x"
    assert body.strip() == "Body"


def test_mapper_defaults_missing_required_variables_with_warning():
    mapper = PromptMapper()
    content = """---
key: simple
name: Simple
version: 1.0.0
description: desc
task_type: test
optional_variables:
  - source_language
default_variables:
  source_language: English
tags:
  - test
---
Hello
"""
    prompt = mapper.to_domain_prompt(content)

    assert prompt.metadata.required_variables == []
    assert any(
        "required_variables" in warning for warning in prompt.metadata.warnings
    )
