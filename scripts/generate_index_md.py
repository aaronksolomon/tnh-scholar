#!/usr/bin/env python3
"""Generate docs/index.md from the actual docs directory structure.

This keeps index.md in sync with the file structure automatically,
ensuring it always reflects what's actually in docs/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import yaml

DOCS_DIR = Path("docs")
INDEX_PATH = DOCS_DIR / "index.md"

# Front matter for the generated index
FRONT_MATTER = """\
---
title: "TNH Scholar Documentation"
description: "Comprehensive documentation for TNH Scholar, an AI-driven project exploring the teachings of Thich Nhat Hanh."
auto_generated: true
---
"""

INTRO = """\
# TNH Scholar Documentation

Welcome to the TNH Scholar documentation. This page maps all available documentation organized by topic.

TNH Scholar is an AI-driven project exploring, processing, and translating the teachings of Thich Nhat Hanh and the Plum Village community through natural language processing and machine learning.

## Documentation Map

"""

def read_title(path: Path) -> Optional[str]:
    """Extract the `title` field from YAML front matter if present."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            try:
                metadata = yaml.safe_load("\n".join(lines[1:idx])) or {}
                title = metadata.get("title")
                return title.strip() if isinstance(title, str) else None
            except yaml.YAMLError:
                return None
    return None


def humanize_name(name: str) -> str:
    """Convert kebab-case to Title Case."""
    return name.replace("-", " ").replace("_", " ").title()


def build_index() -> str:
    """Generate index.md content from docs structure."""
    content = FRONT_MATTER + INTRO
    
    # Group files/dirs by top-level sections
    sections: dict[str, list[tuple[Path, Optional[str]]]] = {}
    
    for item in sorted(DOCS_DIR.iterdir()):
        if item.name.startswith(".") or item.name == "index.md":
            continue
        
        if item.is_dir():
            section_name = item.name
            section_items = []
            
            # Collect markdown files in this section
            for md_file in sorted(item.rglob("*.md")):
                # Skip index files (they're section headers)
                if md_file.name == "index.md":
                    continue
                title = read_title(md_file) or humanize_name(md_file.stem)
                rel_path = md_file.relative_to(DOCS_DIR)
                section_items.append((rel_path, title))
            
            if section_items:
                sections[section_name] = section_items
    
    # Output sections
    for section in sorted(sections.keys()):
        section_title = humanize_name(section)
        content += f"\n### {section_title}\n\n"
        
        for rel_path, title in sections[section]:
            link_path = rel_path.as_posix()
            content += f"- [{title}]({link_path})\n"
    
    return content


def main() -> None:
    content = build_index()
    INDEX_PATH.write_text(content, encoding="utf-8")
    print(f"Generated {INDEX_PATH}")


if __name__ == "__main__":
    main()
