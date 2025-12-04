#!/usr/bin/env python3
"""Generate the literate navigation file consumed by mkdocs-literate-nav."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Iterable

import mkdocs_gen_files
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:  # noqa: E402
    from scripts.sync_root_docs import PROJECT_REPO_DIR, ROOT_DOC_DEST_MAP, ROOT_DOCS
except ModuleNotFoundError:  # Fallback for mkdocs run_path isolation
    sync_path = ROOT / "scripts" / "sync_root_docs.py"
    spec = importlib.util.spec_from_file_location("sync_root_docs", sync_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        PROJECT_REPO_DIR = module.PROJECT_REPO_DIR
        ROOT_DOCS = module.ROOT_DOCS
        ROOT_DOC_DEST_MAP = module.ROOT_DOC_DEST_MAP
    else:
        raise

DOCS_DIR = Path("docs")
NAV_FILENAME = "docs-nav.md"
ROOT_TITLE = "TNH Scholar"
TOP_LEVEL_ORDER = [
    "index.md",
    "getting-started",
    "user-guide",
    "project",
    "community",
    "repo-root",
    "cli-reference",
    "api",
    "architecture",
    "development",
    "docs-ops",
    "research",
]
TITLE_OVERRIDES = {
    "api": "API",
    "cli-reference": "CLI Reference",
    "docs-ops": "Docs Ops",
    "gen-ai-service": "GenAI Service",
    "ai-text-processing": "AI Text Processing",
    "ytt-fetch": "YTT Fetch",
}

TOP_LEVEL_INDEX = {name: idx for idx, name in enumerate(TOP_LEVEL_ORDER)}
DEFAULT_BUCKET = len(TOP_LEVEL_ORDER) + 1


def iter_markdown_files() -> Iterable[Path]:
    """Yield Markdown files under docs/, including mirrored repo-root copies."""
    if not DOCS_DIR.exists():
        return []
    return sorted(DOCS_DIR.rglob("*.md"), key=nav_sort_key)


def nav_sort_key(path: Path) -> tuple:
    """Sort files so curated top-level buckets preserve their intended order."""
    relative = path.relative_to(DOCS_DIR)
    parts = relative.parts
    first = parts[0]
    if parts[: len(PROJECT_REPO_DIR.parts)] == PROJECT_REPO_DIR.parts:
        bucket = TOP_LEVEL_INDEX.get("repo-root", DEFAULT_BUCKET)
    elif len(parts) == 1 and first == "index.md":
        bucket = -1
    else:
        bucket = TOP_LEVEL_INDEX.get(first, DEFAULT_BUCKET)
    is_index = 0 if parts[-1] == "index.md" else 1
    return bucket, parts[:-1], is_index, parts[-1]


def format_name(slug: str) -> str:
    """Humanize directory/file names when front matter does not supply a title."""
    return TITLE_OVERRIDES.get(slug.lower(), slug.replace("-", " ").replace("_", " ").title())


def read_title(path: Path) -> str | None:
    """Extract the `title` field from YAML front matter if present."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        if path.parts[: len(PROJECT_REPO_DIR.parts)] != PROJECT_REPO_DIR.parts:
            return None
        source = Path(path.name)
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            metadata = yaml.safe_load("\n".join(lines[1:idx])) or {}
            title = metadata.get("title")
            return title.strip() if isinstance(title, str) else None
    return None


def build_nav_path(path: Path) -> tuple[str, ...]:
    """Translate a docs-relative path into MkDocs navigation labels."""
    relative = path.relative_to(DOCS_DIR)
    parts = list(relative.with_suffix("").parts)
    if not parts:
        return (ROOT_TITLE,)

    # Special-case mirrored repo-root docs so they appear as "Repo Root/**".
    if parts[: len(PROJECT_REPO_DIR.parts)] == list(PROJECT_REPO_DIR.parts):
        return _extracted_from_build_nav_path_10(parts, path)
    is_index = parts[-1] == "index"
    labels = [format_name(part) for part in parts]
    # If a parent directory has an index with a custom title, reuse it so
    # children stay nested under the same label as the overview page.
    if not is_index and len(parts) > 1:
        parent_index = DOCS_DIR.joinpath(*parts[:-1], "index.md")
        parent_title = read_title(parent_index) if parent_index.exists() else None
        if parent_title:
            labels[-2] = parent_title
    title = read_title(path) or labels[-1]
    if is_index:
        labels = labels[:-1]
        if not labels:
            return (title or ROOT_TITLE,)
        labels[-1] = title
        return tuple(labels)
    labels[-1] = title
    return tuple(labels)


# TODO Rename this here and in `build_nav_path`
def _extracted_from_build_nav_path_10(parts, path):
    remaining = parts[len(PROJECT_REPO_DIR.parts) :]
    is_index = remaining and remaining[-1] == "index"
    labels = ["Repo Root"] + [format_name(part) for part in remaining]
    title = read_title(path) or (labels[-2] if is_index and len(labels) > 1 else labels[-1])
    if is_index:
        # Avoid "Repo Root" nesting; expose index as an overview child.
        return ("Repo Root", "Overview")
    labels[-1] = title
    return tuple(labels)


def main() -> None:
    nav = mkdocs_gen_files.Nav()
    for md_path in iter_markdown_files():
        nav_path = build_nav_path(md_path)
        rel_path = md_path.relative_to(DOCS_DIR).as_posix()
        nav[nav_path] = rel_path
    with mkdocs_gen_files.open(NAV_FILENAME, "w", encoding="utf-8") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


main()
