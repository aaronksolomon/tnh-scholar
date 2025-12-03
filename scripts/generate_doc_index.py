#!/usr/bin/env python3
"""Generate documentation_index.md files from Markdown front matter."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import json

try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    class _MiniYAML:
        @staticmethod
        def safe_load(text: str):
            data = {}
            for line in text.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip().strip('"')
            return data

    yaml = _MiniYAML()  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DOCS_INDEX_PATH = ROOT / "docs/documentation_index.md"

# Exclude these directories from doc index
EXCLUDED_DIRS = {".git", 
                 ".github", 
                 ".mypy_cache", 
                 ".pytest_cache", 
                 ".ruff_cache", 
                 "node_modules", 
                 "site", 
                 "build", 
                 "dist"}


def iter_markdown_files() -> Iterable[Path]:
    """Iterate over all markdown files in repo, excluding common ignored directories."""
    for md_file in sorted(ROOT.rglob("*.md")):
        # Skip files in excluded directories
        if all(excluded not in md_file.parts for excluded in EXCLUDED_DIRS):
            yield md_file


def extract_frontmatter(path: Path) -> dict:
    text = path.read_text()
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                try:
                    data = yaml.safe_load("\n".join(lines[1:idx])) or {}
                except Exception:
                    # Skip files with invalid YAML in frontmatter (e.g., Jinja2 templates)
                    data = {}
                break
        else:
            data = {}
    else:
        data = {}
    return data


def build_index_rows() -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for path in iter_markdown_files():
        rel = path.relative_to(ROOT).as_posix()
        meta = extract_frontmatter(path)
        title = meta.get("title", path.stem)
        desc = meta.get("description", "")
        created = meta.get("created", "")
        if isinstance(desc, str):
            desc = desc.replace("|", "\\|")
        rows.append((rel, title, desc, created))
    return rows


def write_index(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    """Generate documentation index with relative links (docs-only)."""
    header = [
        "---",
        'title: "Documentation Index"',
        'description: "Complete index of TNH Scholar documentation"',
        'owner: ""',
        'author: ""',
        'status: processing',
        f'created: "{datetime.now(timezone.utc).date()}"',
        "auto_generated: true",
        "---",
        "",
        "# Documentation Index",
        "",
        "| Path | Title | Description | Created |",
        "| --- | --- | --- | --- |",
    ]
    # Convert absolute paths to relative (strip "docs/" prefix)
    body = []
    for rel, title, desc, created in rows:
        doc_path = rel[5:] if rel.startswith("docs/") else rel  # Remove "docs/" prefix
        body.append(f"| [{rel}]({doc_path}) | {title} | {desc} | {created} |")
    path.write_text("\n".join(header + body) + "\n")


def main() -> None:
    all_rows = build_index_rows()
    # Filter to only docs/ files for documentation index
    docs_rows = [r for r in all_rows if r[0].startswith("docs/")]
    DOCS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_index(DOCS_INDEX_PATH, docs_rows)


if __name__ == "__main__":
    main()
