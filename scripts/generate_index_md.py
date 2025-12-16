#!/usr/bin/env python3
"""Maintain the Documentation Map section in docs/index.md.

If docs/index.md declares `auto_generated: true` in its front matter, the
entire file is regenerated (legacy behavior). Otherwise, only the
`## Documentation Map` section is replaced while preserving curated content
above it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

DOCS_DIR = Path("docs")
INDEX_PATH = DOCS_DIR / "index.md"
MAP_HEADING = "## Documentation Map"


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


def as_absolute_link(path: str) -> str:
    """Normalize links to absolute paths rooted at docs/."""
    return "/" + path.lstrip("/")


def build_map_content() -> str:
    """Generate the documentation map list grouped by top-level section."""
    sections: dict[str, list[tuple[Path, Optional[str]]]] = {}

    for item in sorted(DOCS_DIR.iterdir()):
        if item.name.startswith(".") or item.name == "index.md":
            continue

        if item.is_dir():
            section_items: list[tuple[Path, Optional[str]]] = []
            for md_file in sorted(item.rglob("*.md")):
                if md_file.name == "index.md":
                    continue
                title = read_title(md_file) or humanize_name(md_file.stem)
                section_items.append((md_file.relative_to(DOCS_DIR), title))

            if section_items:
                sections[item.name] = section_items

    lines: list[str] = []
    for section in sorted(sections.keys()):
        section_title = humanize_name(section)
        lines.append(f"### {section_title}")
        lines.append("")
        for rel_path, title in sections[section]:
            lines.append(f"- [{title}]({as_absolute_link(rel_path.as_posix())})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_front_matter(text: str) -> tuple[dict, list[str]]:
    """Return front matter dict and remaining lines (without markers)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            metadata = yaml.safe_load("\n".join(lines[1:idx])) or {}
            return metadata, lines[idx + 1 :]
    return {}, lines


def regenerate_full() -> str:
    """Legacy behavior: regenerate the entire index."""
    front_matter = {
        "title": "TNH Scholar Documentation",
        "description": "Comprehensive documentation for TNH Scholar, an AI-driven project exploring the teachings of Thich Nhat Hanh.",
        "auto_generated": True,
    }
    fm = "---\n" + yaml.safe_dump(front_matter, sort_keys=False).rstrip() + "\n---\n\n"
    intro = (
        "# TNH Scholar Documentation\n\n"
        "Welcome to the TNH Scholar documentation. This page maps all available documentation organized by topic.\n\n"
        "TNH Scholar is an AI-driven project exploring, processing, and translating the teachings of Thich Nhat Hanh "
        "and the Plum Village community through natural language processing and machine learning.\n\n"
        f"{MAP_HEADING}\n\n"
    )
    return fm + intro + build_map_content()


def update_map_section(existing_text: str) -> str:
    """Preserve curated content and replace only the Documentation Map section."""
    metadata, body_lines = parse_front_matter(existing_text)
    map_heading_idx = next((i for i, line in enumerate(body_lines) if line.strip() == MAP_HEADING), None)

    if map_heading_idx is None:
        # Append a new map section at the end
        new_body = body_lines + ["", MAP_HEADING, "", build_map_content().rstrip(), ""]
    else:
        before_map = body_lines[: map_heading_idx + 1]
        after_heading = body_lines[map_heading_idx + 1 :]

        # Preserve any descriptive lines immediately following the heading until a blank line
        preserved: list[str] = []
        rest_start = 0
        for idx, line in enumerate(after_heading):
            if line.strip() == "":
                preserved = after_heading[: idx + 1]
                rest_start = idx + 1
                break
        else:
            preserved = after_heading
            rest_start = len(after_heading)

        new_body = before_map + preserved + [build_map_content().rstrip(), ""]

        # If there was additional content after the map, append it
        if rest_start < len(after_heading):
            # Skip existing map content until the next heading at the same level
            remainder = after_heading[rest_start:]
            next_heading = next((i for i, line in enumerate(remainder) if line.startswith("## ")), None)
            if next_heading is not None:
                new_body += remainder[next_heading:]

    if metadata:
        fm = "---\n" + yaml.safe_dump(metadata, sort_keys=False).rstrip() + "\n---\n\n"
    else:
        fm = ""

    # Strip leading empty lines from body to avoid accumulating blank lines
    while new_body and new_body[0].strip() == "":
        new_body.pop(0)

    return fm + "\n".join(new_body).rstrip() + "\n"


def main() -> None:
    existing = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
    metadata, _ = parse_front_matter(existing)
    if metadata.get("auto_generated") is True:
        content = regenerate_full()
        INDEX_PATH.write_text(content, encoding="utf-8")
        print(f"Generated {INDEX_PATH} (auto_generated: true)")
    else:
        updated = update_map_section(existing)
        INDEX_PATH.write_text(updated, encoding="utf-8")
        print(f"Updated Documentation Map in {INDEX_PATH} (curated content preserved)")


if __name__ == "__main__":
    main()
