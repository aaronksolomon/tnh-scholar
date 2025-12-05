#!/usr/bin/env python3
"""Append documentation_map.md content to index.md during build."""
from __future__ import annotations

from pathlib import Path

import mkdocs_gen_files

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
INDEX_PATH = DOCS_DIR / "index.md"
DOC_MAP_PATH = DOCS_DIR / "documentation_map.md"


def main() -> None:
    """Append documentation map to index.md."""
    if not INDEX_PATH.exists() or not DOC_MAP_PATH.exists():
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

    # Find where the static Documentation Map section starts in index.md
    # We'll replace everything from "## Documentation Map" onwards
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

    # Write the combined content using mkdocs_gen_files
    with mkdocs_gen_files.open("index.md", "w", encoding="utf-8") as f:
        f.write(combined)


if __name__ == "__main__":
    main()
else:
    main()  # Also run when imported by mkdocs
