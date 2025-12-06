#!/usr/bin/env python3
"""Generate documentation_index.md and documentation_map.md from Markdown front matter."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

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
DOCS_DIR = ROOT / "docs"
DOCS_INDEX_PATH = DOCS_DIR / "documentation_index.md"
DOCS_MAP_PATH = DOCS_DIR / "documentation_map.md"

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

# Files to exclude from navigation (should match mkdocs.yaml exclude_docs)
EXCLUDE_PATTERNS = [
    "archive/index-old.md",
    "tnh-index-updated.md",
    "documentation_index.md",  # Don't include itself
    "documentation_map.md",     # Don't include itself
]

# Category display order and titles (matches generate_mkdocs_nav.py)
CATEGORY_ORDER = [
    "index.md",
    "getting-started",
    "user-guide",
    "project",
    "community",
    "cli-reference",
    "api",
    "architecture",
    "development",
    "docs-ops",
    "research",
]

CATEGORY_TITLES = {
    "getting-started": "Getting Started",
    "user-guide": "User Guide",
    "project": "Project",
    "community": "Community",
    "cli-reference": "CLI Reference",
    "api": "API",
    "architecture": "Architecture",
    "development": "Development",
    "docs-ops": "Docs Ops",
    "research": "Research",
}


def should_exclude(rel_path: str) -> bool:
    """Check if file should be excluded based on EXCLUDE_PATTERNS."""
    return any(
        rel_path == pattern or rel_path.startswith(pattern.rstrip('/') + '/')
        for pattern in EXCLUDE_PATTERNS
    )


def iter_markdown_files() -> Iterable[Path]:
    """Iterate over docs/ markdown files, excluding patterns."""
    if not DOCS_DIR.exists():
        return

    for md_file in DOCS_DIR.rglob("*.md"):
        if not md_file.is_file():
            continue

        rel_path = md_file.relative_to(DOCS_DIR).as_posix()

        # Skip excluded patterns
        if should_exclude(rel_path):
            continue

        # Skip files in excluded directories
        if any(excluded in md_file.parts for excluded in EXCLUDED_DIRS):
            continue

        yield md_file


def extract_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from markdown file."""
    try:
        text = path.read_text()
    except (UnicodeDecodeError, FileNotFoundError):
        return {}

    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                try:
                    data = yaml.safe_load("\n".join(lines[1:idx])) or {}
                except Exception:
                    data = {}
                return data
    return {}


def get_category(rel_path: str) -> str:
    """Extract category from file path (top-level directory)."""
    parts = rel_path.split("/")
    if len(parts) == 1:
        return "Root"
    return parts[0]


def format_category_title(category: str) -> str:
    """Get human-readable category title."""
    return CATEGORY_TITLES.get(category, category.replace("-", " ").title())


def build_file_data() -> list[dict]:
    """Build list of file metadata dicts."""
    files = []
    for path in iter_markdown_files():
        rel_path = path.relative_to(DOCS_DIR).as_posix()
        meta = extract_frontmatter(path)

        title = meta.get("title", path.stem)
        desc = meta.get("description", "")
        created = meta.get("created", "")
        category = get_category(rel_path)

        # Escape pipe characters in description for table format
        if isinstance(desc, str):
            desc = desc.replace("|", "\\|")

        files.append({
            "path": rel_path,
            "title": title,
            "description": desc,
            "created": created,
            "category": category,
        })

    return files


def write_documentation_map(path: Path, files: list[dict]) -> None:
    """Generate hierarchical documentation map (for appending to index.md)."""
    # Filter out index.md files (navigation landing pages) except root-level
    filtered_files = [
        f for f in files
        if not (f["path"].endswith("/index.md") or f["path"] == "index.md")
    ]

    # Group by category
    by_category = defaultdict(list)
    for file in filtered_files:
        by_category[file["category"]].append(file)

    # Sort categories by CATEGORY_ORDER, then alphabetically
    def category_sort_key(cat: str) -> tuple:
        try:
            return (0, CATEGORY_ORDER.index(cat))
        except ValueError:
            return (1, cat)

    sorted_categories = sorted(by_category.keys(), key=category_sort_key)

    # Build output
    lines = [
        "---",
        'title: "Documentation Map"',
        'description: "Hierarchical navigation of TNH Scholar documentation"',
        f'created: "{datetime.now(timezone.utc).date()}"',
        "auto_generated: true",
        "---",
        "",
        "# Documentation Map",
        "",
    ]

    for category in sorted_categories:
        if category == "Root":
            continue  # Skip root-level files

        category_title = format_category_title(category)
        lines.append(f"## {category_title}")
        lines.append("")

        # Sort files within category by title
        category_files = sorted(by_category[category], key=lambda f: f["title"].lower())

        for file in category_files:
            # Simple list format with title and link
            lines.append(f"- [{file['title']}]({file['path']})")

        lines.append("")

    path.write_text("\n".join(lines))


def write_documentation_index(path: Path, files: list[dict]) -> None:
    """Generate comprehensive documentation index with tables by category."""
    # Group by category
    by_category = defaultdict(list)
    for file in files:
        by_category[file["category"]].append(file)

    # Sort categories
    def category_sort_key(cat: str) -> tuple:
        try:
            return (0, CATEGORY_ORDER.index(cat))
        except ValueError:
            return (1, cat)

    sorted_categories = sorted(by_category.keys(), key=category_sort_key)

    # Build output
    lines = [
        "---",
        'title: "Documentation Index"',
        'description: "Complete searchable index of TNH Scholar documentation with metadata"',
        f'created: "{datetime.now(timezone.utc).date()}"',
        "auto_generated: true",
        "---",
        "",
        "# Documentation Index",
        "",
        "This is a comprehensive, searchable index of all TNH Scholar documentation with descriptions and metadata.",
        "",
        "For a simpler hierarchical view, see the Documentation Map section at the bottom of the [main index](index.md).",
        "",
    ]

    for category in sorted_categories:
        category_title = format_category_title(category)
        lines.append(f"## {category_title}")
        lines.append("")

        # Table header
        lines.append("| Title | Description | Created | Path |")
        lines.append("| --- | --- | --- | --- |")

        # Sort files within category by title
        category_files = sorted(by_category[category], key=lambda f: f["title"].lower())

        for file in category_files:
            lines.append(
                f"| [{file['title']}]({file['path']}) | {file['description']} | "
                f"{file['created']} | `docs/{file['path']}` |"
            )

        lines.append("")

    path.write_text("\n".join(lines))


def main() -> None:
    """Generate both documentation_index.md and documentation_map.md."""
    files = build_file_data()

    DOCS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)

    write_documentation_index(DOCS_INDEX_PATH, files)
    write_documentation_map(DOCS_MAP_PATH, files)

    print(f"Generated {DOCS_INDEX_PATH.relative_to(ROOT)}")
    print(f"Generated {DOCS_MAP_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
