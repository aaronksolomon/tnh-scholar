#!/usr/bin/env python3
"""Generate auto index.md files for docs subdirectories."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    class _MiniYAML:
        @staticmethod
        def safe_load(text: str) -> Dict:
            data: Dict[str, str] = {}
            for line in text.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip().strip('"')
            return data

    yaml = _MiniYAML()  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
AUTO_FLAG = "auto_generated"

EXCLUDED_DIRS = {
    ".git",
    ".github",
    "site",
    "build",
    "dist",
    "__pycache__",
}

TITLE_OVERRIDES = {
    "cli-reference": "CLI Reference",
    "api": "API",
    "docs-ops": "Docs Ops",
}


def parse_frontmatter(path: Path) -> Dict:
    """Return frontmatter dict if present, else {}."""
    try:
        text = path.read_text()
    except FileNotFoundError:
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            try:
                return yaml.safe_load("\n".join(lines[1:idx])) or {}
            except Exception:
                return {}
    return {}


def title_from_dir(dirname: str) -> str:
    override = TITLE_OVERRIDES.get(dirname.lower())
    if override:
        return override
    return dirname.replace("-", " ").replace("_", " ").title()


def iter_docs_dirs() -> List[Path]:
    """Yield subdirectories under docs (excluding root docs itself)."""
    dirs: List[Path] = []
    for path in DOCS_ROOT.rglob("*"):
        if not path.is_dir():
            continue
        rel_parts = path.relative_to(DOCS_ROOT).parts
        if not rel_parts:
            continue  # skip root docs
        if all(part not in EXCLUDED_DIRS for part in rel_parts):
            dirs.append(path)
    return sorted(dirs)


def collect_entries(directory: Path) -> List[Tuple[str, str, str, str]]:
    """Return list of (link_relative_to_dir, title, description, display_path) for direct children."""
    entries: List[Tuple[str, str, str, str]] = []
    rel_dir = directory.relative_to(DOCS_ROOT)

    # markdown files in this dir (excluding index.md)
    for md in sorted(directory.glob("*.md")):
        if md.name == "index.md":
            continue
        meta = parse_frontmatter(md)
        title = meta.get("title", md.stem)
        desc = meta.get("description", "")
        rel_link = md.name  # link relative to current directory
        display_path = md.relative_to(DOCS_ROOT).as_posix()
        entries.append((rel_link, title, desc, display_path))

    # subdirectories with their index.md
    for subdir in sorted(p for p in directory.iterdir() if p.is_dir()):
        # Avoid nesting mirrored repo-root docs under project TOC.
        if rel_dir == Path("project") and subdir.name == "repo-root":
            continue
        index_file = subdir / "index.md"
        if not index_file.exists():
            continue
        meta = parse_frontmatter(index_file)
        title = meta.get("title", title_from_dir(subdir.name))
        desc = meta.get("description", "")
        rel_link = f"{subdir.name}/index.md"  # relative to current directory
        display_path = index_file.relative_to(DOCS_ROOT).as_posix()
        entries.append((rel_link, title, desc, display_path))

    return entries


def should_generate(index_path: Path) -> bool:
    if not index_path.exists():
        return True
    meta = parse_frontmatter(index_path)
    val = meta.get(AUTO_FLAG)
    if isinstance(val, bool):
        return val
    return val.strip().lower() == "true" if isinstance(val, str) else False


def write_index(directory: Path, entries: List[Tuple[str, str, str, str]]) -> None:
    rel_dir = directory.relative_to(DOCS_ROOT).as_posix()
    index_path = directory / "index.md"
    title = title_from_dir(directory.name)
    header = [
        "---",
        f'title: "{title}"',
        f'description: "Table of contents for {rel_dir}"',
        'owner: ""',
        'author: ""',
        'status: processing',
        f'created: "{datetime.now(timezone.utc).date()}"',
        f"{AUTO_FLAG}: true",
        "---",
        "",
        f"# {title}",
        "",
        "**Table of Contents**:",
        "",
        f"<!-- To manually edit this file, update the front matter and keep `{AUTO_FLAG}: true` to allow regeneration. -->",
        "",
    ]
    body: list = []
    for rel_link, item_title, desc, _ in entries:
        if desc:
            body.append(f"**[{item_title}]({rel_link})** - {desc}")
        else:
            body.append(f"**[{item_title}]({rel_link})**")
        body.append("")
    footer = [
        "---",
        "",
        "*This file auto-generated.*",
    ]
    index_path.write_text("\n".join(header + body + footer) + "\n")


def main() -> None:
    for directory in iter_docs_dirs():
        index_path = directory / "index.md"
        if not should_generate(index_path):
            continue
        if entries := collect_entries(directory):
            write_index(directory, entries)


if __name__ == "__main__":
    main()
