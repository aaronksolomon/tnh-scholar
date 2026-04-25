#!/usr/bin/env python3
"""Update docs/index.md with the latest documentation map content.

This script updates the source docs/index.md file by replacing everything from
"## Documentation Map" onwards with the content from documentation_map.md.

Run this after generate_doc_index.py to sync the source index.md with the
auto-generated documentation map.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
INDEX_PATH = DOCS_DIR / "index.md"
DOC_MAP_PATH = DOCS_DIR / "documentation_map.md"


def extract_doc_map_content(doc_map_content: str) -> str:
    """Return documentation map content without front matter or title."""
    lines = doc_map_content.splitlines()
    start_idx = 0
    if lines and lines[0].strip() == "---":
        for idx, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                start_idx = idx + 1
                break

    while start_idx < len(lines):
        line = lines[start_idx].strip()
        if line and not line.startswith("# Documentation Map"):
            break
        start_idx += 1

    return "\n".join(lines[start_idx:])


def replace_index_map(index_content: str, map_content: str) -> str:
    """Replace or append the Documentation Map section."""
    index_lines = index_content.splitlines()
    for idx, line in enumerate(index_lines):
        if line.strip() == "## Documentation Map":
            before_map = "\n".join(index_lines[:idx])
            return before_map.rstrip() + "\n\n## Documentation Map\n\n" + map_content + "\n"
    return index_content.rstrip() + "\n\n## Documentation Map\n\n" + map_content + "\n"


def main() -> None:
    """Update docs/index.md with documentation map content."""
    if not INDEX_PATH.exists() or not DOC_MAP_PATH.exists():
        print("Error: index.md or documentation_map.md not found")
        return

    index_content = INDEX_PATH.read_text()
    doc_map_content = DOC_MAP_PATH.read_text()
    map_content = extract_doc_map_content(doc_map_content)
    combined = replace_index_map(index_content, map_content)

    INDEX_PATH.write_text(combined)
    print(f"Updated {INDEX_PATH.relative_to(ROOT)} with documentation map")


if __name__ == "__main__":
    main()
