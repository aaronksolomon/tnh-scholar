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


def main() -> None:
    """Update docs/index.md with documentation map content."""
    if not INDEX_PATH.exists() or not DOC_MAP_PATH.exists():
        print("Error: index.md or documentation_map.md not found")
        return

    # Read the base index.md
    index_content = INDEX_PATH.read_text()

    # Read documentation_map.md and extract content (skip frontmatter and title)
    doc_map_content = DOC_MAP_PATH.read_text()
    lines = doc_map_content.splitlines()

    # Skip frontmatter
    start_idx = 0
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                start_idx = idx + 1
                break

    # Skip empty lines and the "# Documentation Map" title
    while start_idx < len(lines):
        line = lines[start_idx].strip()
        if line and not line.startswith("# Documentation Map"):
            break
        start_idx += 1

    # Get the content to append (everything after frontmatter and title)
    map_content_lines = lines[start_idx:]
    map_content = "\n".join(map_content_lines)

    # Find where the Documentation Map section starts in index.md
    index_lines = index_content.splitlines()
    doc_map_start = None

    for idx, line in enumerate(index_lines):
        if line.strip() == "## Documentation Map":
            doc_map_start = idx
            break

    if doc_map_start is None:
        # No Documentation Map section found, append at end
        combined = index_content.rstrip() + "\n\n## Documentation Map\n\n" + map_content + "\n"
    else:
        # Replace everything from Documentation Map section onwards
        before_map = "\n".join(index_lines[:doc_map_start])
        combined = before_map.rstrip() + "\n\n## Documentation Map\n\n" + map_content + "\n"

    # Write the combined content back to source index.md
    INDEX_PATH.write_text(combined)
    print(f"Updated {INDEX_PATH.relative_to(ROOT)} with documentation map")


if __name__ == "__main__":
    main()
