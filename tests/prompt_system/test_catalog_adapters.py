from pathlib import Path

import pytest

from tnh_scholar.prompt_system.adapters.filesystem_catalog_adapter import (
    FilesystemPromptCatalog,
)
from tnh_scholar.prompt_system.config.prompt_catalog_config import PromptCatalogConfig
from tnh_scholar.prompt_system.config.policy import ValidationPolicy
from tnh_scholar.prompt_system.domain.models import PromptValidationResult
from tnh_scholar.prompt_system.mappers.prompt_mapper import PromptMapper
from tnh_scholar.prompt_system.service.loader import PromptLoader
from tnh_scholar.prompt_system.service.validator import PromptValidator


def write_prompt(tmp_path: Path, name: str, template: str = "Hello"):
    content = f"""---
key: {name}
name: {name}
version: 1.0.0
description: desc
task_type: test
required_variables: []
---
{template}
"""
    (tmp_path / f"{name}.md").write_text(content, encoding="utf-8")


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


def test_mapper_split_handles_bom_and_delimiters():
    mapper = PromptMapper()
    content = "\ufeff---\nkey: x\nname: x\nversion: 1.0.0\ndescription: d\ntask_type: t\nrequired_variables: []\n---\nBody"
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
