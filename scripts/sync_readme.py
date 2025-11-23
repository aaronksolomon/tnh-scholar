#!/usr/bin/env python3
"""Verify README.md and docs/index.md are synchronized."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
DOCS_INDEX_PATH = ROOT / "docs/index.md"


def extract_section_headings(path: Path) -> set[str]:
    """Extract all H2 headings (##) from markdown file."""
    if not path.exists():
        return set()
    
    text = path.read_text()
    headings = set()
    for line in text.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            headings.add(heading)
    
    return headings


def main() -> None:
    """Check README and docs/index.md sync."""
    print("Checking README ↔ docs/index.md synchronization...")
    
    readme_sections = extract_section_headings(README_PATH)
    docs_sections = extract_section_headings(DOCS_INDEX_PATH)
    
    missing_in_readme = docs_sections - readme_sections
    missing_in_docs = readme_sections - docs_sections
    
    warnings = []
    
    if missing_in_readme:
        warnings.append(f"  ⚠ Missing in README.md: {', '.join(sorted(missing_in_readme))}")
    
    if missing_in_docs:
        warnings.append(f"  ⚠ Missing in docs/index.md: {', '.join(sorted(missing_in_docs))}")
    
    if warnings:
        print("\nDivergences found:")
        for w in warnings:
            print(w)
        print("\nNote: Minor divergences are OK (intro material, examples).")
        print("Major section outlines should align between README and docs/index.md.")
        return 1
    else:
        print("✓ README and docs/index.md sections are synchronized")
        return 0


if __name__ == "__main__":
    sys.exit(main())
