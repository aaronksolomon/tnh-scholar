#!/usr/bin/env python3
"""Generate documentation_index.md files from Markdown front matter."""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATHS = [ROOT / "documentation_index.md", ROOT / "docs/docs-ops/documentation_index.md"]


def iter_markdown_files() -> Iterable[Path]:
    result = subprocess.run(
        ["rg", "--files", "-g", "*.md"], capture_output=True, text=True, check=True
    )
    for line in sorted(result.stdout.splitlines()):
        line = line.strip()
        if line:
            yield ROOT / line


def extract_frontmatter(path: Path) -> dict:
    text = path.read_text()
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                data = yaml.safe_load("\n".join(lines[1:idx])) or {}
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
    header = [
        "---",
        'title: "Documentation Index"',
        'description: "Inventory of Markdown sources"',
        'owner: ""',
        'author: ""',
        'status: processing',
        f'created: "{datetime.utcnow().date()}"',
        "auto_generated: true",
        "---",
        "",
        "# Documentation Index",
        "",
        "| Path | Title | Description | Created |",
        "| --- | --- | --- | --- |",
    ]
    body = [f"| [{rel}]({rel}) | {title} | {desc} | {created} |" for rel, title, desc, created in rows]
    path.write_text("\n".join(header + body) + "\n")


def main() -> None:
    rows = build_index_rows()
    for index_path in INDEX_PATHS:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        write_index(index_path, rows)


if __name__ == "__main__":
    main()
