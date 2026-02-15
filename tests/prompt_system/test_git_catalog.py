import subprocess
from pathlib import Path
from types import SimpleNamespace

from tnh_scholar.prompt_system.adapters.git_catalog_adapter import GitPromptCatalog
from tnh_scholar.prompt_system.config.policy import ValidationPolicy
from tnh_scholar.prompt_system.config.prompt_catalog_config import (
    GitTransportConfig,
    PromptCatalogConfig,
)
from tnh_scholar.prompt_system.mappers.prompt_mapper import PromptMapper
from tnh_scholar.prompt_system.service.loader import PromptLoader
from tnh_scholar.prompt_system.service.validator import PromptValidator
from tnh_scholar.prompt_system.transport.git_client import GitTransportClient


def _init_git_repo(repo_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)


def _write_prompt(repo_path: Path, name: str, template: str = "Hi {{who}}"):
    prompt_path = repo_path / f"{name}.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_name = name.split("/")[-1]
    content = f"""---
key: {name}
name: {prompt_name}
version: 1.0.0
description: desc
task_type: test
required_variables:
  - who
---
{template}
"""
    prompt_path.write_text(content, encoding="utf-8")


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


def test_git_catalog_loads_namespaced_prompt_with_immutable_key(tmp_path: Path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _init_git_repo(repo_path)
    _write_prompt(repo_path, "agent-orch/planner/evaluate_harness_report")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "add namespaced prompt"],
        cwd=repo_path,
        check=True,
        stdout=subprocess.PIPE,
    )

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

    prompt = catalog.get("agent-orch/planner/evaluate_harness_report.v1")

    assert prompt.metadata.canonical_key() == "agent-orch/planner/evaluate_harness_report"


def test_git_catalog_list_returns_namespaced_keys(tmp_path: Path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _init_git_repo(repo_path)
    _write_prompt(repo_path, "agent-orch/planner/evaluate")
    _write_prompt(repo_path, "core/task/summarize")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "add prompt set"],
        cwd=repo_path,
        check=True,
        stdout=subprocess.PIPE,
    )

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

    keys = sorted(metadata.canonical_key() for metadata in catalog.list())

    assert keys == ["agent-orch/planner/evaluate", "core/task/summarize"]


def test_git_catalog_uses_cache_for_repeated_loads(tmp_path: Path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _init_git_repo(repo_path)
    _write_prompt(repo_path, "sample", "First")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "add sample"],
        cwd=repo_path,
        check=True,
        stdout=subprocess.PIPE,
    )

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

    first = catalog.get("sample")
    (repo_path / "sample.md").write_text(
        "not a valid frontmatter payload",
        encoding="utf-8",
    )
    second = catalog.get("sample")

    assert first.template == second.template


def test_git_catalog_falls_back_on_validation_errors(tmp_path: Path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _init_git_repo(repo_path)
    (repo_path / "bad-json.md").write_text(
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
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "add bad prompt"],
        cwd=repo_path,
        check=True,
        stdout=subprocess.PIPE,
    )

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

    prompt = catalog.get("bad-json")

    assert prompt.metadata.version == "1"
    assert prompt.template.strip() == "{{ result }}"
    assert any("Invalid prompt" in warning for warning in prompt.metadata.warnings)


def test_git_catalog_refresh_invalidates_changed_keys(tmp_path: Path, monkeypatch):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _init_git_repo(repo_path)
    _write_prompt(repo_path, "agent-orch/planner/evaluate")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "add prompt"],
        cwd=repo_path,
        check=True,
        stdout=subprocess.PIPE,
    )

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

    invalidated: list[str] = []
    monkeypatch.setattr(
        catalog._cache,
        "invalidate",
        invalidated.append,
    )
    monkeypatch.setattr(
        transport,
        "pull_latest",
        lambda: SimpleNamespace(changed_files=["agent-orch/planner/evaluate.md"]),
    )

    catalog.refresh()

    assert len(invalidated) == 1
    assert invalidated[0].startswith("agent-orch/planner/evaluate@")
