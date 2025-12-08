import subprocess
from pathlib import Path

from tnh_scholar.prompt_system.adapters.git_catalog_adapter import GitPromptCatalog
from tnh_scholar.prompt_system.config.prompt_catalog_config import (
    GitTransportConfig,
    PromptCatalogConfig,
)
from tnh_scholar.prompt_system.config.policy import ValidationPolicy
from tnh_scholar.prompt_system.mappers.prompt_mapper import PromptMapper
from tnh_scholar.prompt_system.service.loader import PromptLoader
from tnh_scholar.prompt_system.service.validator import PromptValidator
from tnh_scholar.prompt_system.transport.git_client import GitTransportClient


def _init_git_repo(repo_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)


def _write_prompt(repo_path: Path, name: str, template: str = "Hi {{who}}"):
    content = f"""---
key: {name}
name: {name}
version: 1.0.0
description: desc
task_type: test
required_variables:
  - who
---
{template}
"""
    (repo_path / f"{name}.md").write_text(content, encoding="utf-8")


def test_git_catalog_loads_prompt(tmp_path: Path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _init_git_repo(repo_path)
    _write_prompt(repo_path, "sample")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "add sample"], cwd=repo_path, check=True, stdout=subprocess.PIPE)

    transport_config = GitTransportConfig(repository_path=repo_path, auto_pull=False)
    mapper = PromptMapper()
    validator = PromptValidator(ValidationPolicy())
    loader = PromptLoader(validator)
    transport = GitTransportClient(config=transport_config, mapper=mapper)

    catalog_config = PromptCatalogConfig(repository_path=repo_path, enable_git_refresh=False)
    catalog = GitPromptCatalog(
        config=catalog_config,
        transport=transport,
        loader=loader,
        mapper=mapper,
    )

    prompt = catalog.get("sample")
    assert prompt.metadata.name == "sample"
    assert "Hi" in prompt.template
