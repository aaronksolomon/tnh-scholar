#!/usr/bin/env python3
"""Sync root-level markdown files into the docs site at build time.

Uses mkdocs-gen-files to generate read-only copies under `project/` so the
MkDocs navigation can expose repository metadata without adding files to the
working tree.
"""
from __future__ import annotations

import re
import shutil
from typing import Tuple
from pathlib import Path
import json

try:
    import yaml  # type: ignore
    YAMLError = yaml.YAMLError
except ModuleNotFoundError:
    class _MiniYAML:
        YAMLError = ValueError

        @staticmethod
        def safe_load(text: str):
            data = {}
            for line in text.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip().strip('"')
            return data

        @staticmethod
        def safe_dump(data, sort_keys: bool = False) -> str:
            lines = []
            for k, v in data.items():
                lines.append(f"{k}: {json.dumps(v)}")
            return "\n".join(lines)

    yaml = _MiniYAML()  # type: ignore
    YAMLError = _MiniYAML.YAMLError

try:
    import mkdocs_gen_files  # type: ignore
except ModuleNotFoundError:
    class _DummyGenFiles:
        @staticmethod
        def open(path: str, mode: str = "r", encoding: str | None = None):
            return open(path, mode, encoding=encoding)

        @staticmethod
        def set_edit_path(*args, **kwargs):
            return None

    mkdocs_gen_files = _DummyGenFiles()  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
# Destination under docs/ for mirrored repo-root docs.
PROJECT_REPO_DIR = Path("project") / "repo-root"
DOCS_DIR = ROOT / "docs"
GITHUB_ROOT = "https://github.com/aaronksolomon/tnh-scholar/blob/main/"

# Root-level markdown files to surface in the documentation site.
ROOT_DOCS: Tuple[str, ...] = (
    "README.md",
    "TODO.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "DEV_SETUP.md",
    "release_checklist.md",
)
# Keep generated docs aligned with the current docs/ structure (lowercase, hyphenated names).
ROOT_DOC_DEST_MAP = {
    "README.md": "repo-readme.md",
    "TODO.md": "todo-list.md",
    "CHANGELOG.md": "changelog.md",
    "CONTRIBUTING.md": "contributing-root.md",
    "DEV_SETUP.md": "dev-setup-guide.md",
    "release_checklist.md": "release_checklist.md",
}

WARNING_TEMPLATE = "<!-- DO NOT EDIT: Auto-generated from /{name}. Edit the root file instead. -->"

# Convert repo-root doc links like docs/architecture/... to site-relative ../architecture/...
DOC_LINK_PATTERN = re.compile(r"\((?:\./)?docs/")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def humanize(name: str) -> str:
    """Basic title fallback when no front matter title exists."""
    return name.replace("_", " ").replace("-", " ").replace(".md", "").title()


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Return front matter dict (if any) and the remaining body text."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                try:
                    metadata = yaml.safe_load("\n".join(lines[1:idx])) or {}
                except YAMLError:
                    metadata = {}
                body = "\n".join(lines[idx + 1 :]).lstrip("\n")
                return metadata, body
    return {}, text


def rewrite_links(body: str, dest_rel: Path) -> str:
    """Adjust links so generated copies resolve in the docs site."""
    # Number of parent hops from dest back to docs/ root (exclude the filename).
    prefix = "../" * (len(dest_rel.parts) - 1)
    body = DOC_LINK_PATTERN.sub(f"({prefix}", body)

    def replace_link(match: re.Match) -> str:
        text, url = match.group(1), match.group(2)
        if url.startswith(("#", "mailto:", "http://", "https://")):
            return match.group(0)
        if url.startswith("../") or url.startswith(prefix):
            return match.group(0)
        if url.startswith("project/"):
            return match.group(0)
        # Default: point to GitHub root for non-doc, repo-relative references.
        rewritten = GITHUB_ROOT + url.lstrip("./")
        return f"[{text}]({rewritten})"

    return MARKDOWN_LINK_PATTERN.sub(replace_link, body)


def read_title(path: Path) -> str | None:
    """Extract title from YAML front matter if present."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    metadata, _ = parse_front_matter(text)
    title = metadata.get("title")
    return title.strip() if isinstance(title, str) else None


def build_generated_content(source: Path, dest_rel: Path) -> str:
    """Render the generated file with preserved metadata and warning banner."""
    text = source.read_text(encoding="utf-8")
    metadata, body = parse_front_matter(text)
    metadata = metadata or {}
    metadata["auto_generated"] = True
    metadata.setdefault("generated_from", f"/{source.name}")

    warning = WARNING_TEMPLATE.format(name=source.name)
    fm = "---\n" + yaml.safe_dump(metadata, sort_keys=False).rstrip() + "\n---\n\n"
    body = rewrite_links(body, dest_rel).rstrip() + "\n"
    return fm + warning + "\n\n" + body


def write_file(rel_path: Path, content: str, edit_source: str) -> None:
    """Write to mkdocs virtual FS if available and to disk for discovery."""
    dest_str = rel_path.as_posix()
    try:
        with mkdocs_gen_files.open(dest_str, "w", encoding="utf-8") as f:
            f.write(content)
        mkdocs_gen_files.set_edit_path(dest_str, edit_source)
    except Exception:
        # Outside mkdocs-gen-files context (e.g., standalone run)
        pass

    dest_fs = DOCS_DIR / rel_path
    dest_fs.parent.mkdir(parents=True, exist_ok=True)
    dest_fs.write_text(content, encoding="utf-8")


def write_project_docs() -> None:
    for name in ROOT_DOCS:
        source = ROOT / name
        if not source.exists():
            continue
        dest_name = ROOT_DOC_DEST_MAP[name]
        dest_rel = PROJECT_REPO_DIR / dest_name
        content = build_generated_content(source, dest_rel)
        write_file(dest_rel, content, f"/{name}")


def write_index() -> None:
    """Generate docs/project/repo-root/index.md with a short description."""
    lines = [
        "---",
        'title: "Repo Root"',
        'description: "Repository root documentation surfaced in the MkDocs site."',
        "auto_generated: true",
        "---",
        "",
        "# Repo Root",
        "",
        "Repository root documents are mirrored here for discoverability. ",
        "Edit the originals in the repository root; these copies are generated during the docs build.",
        "",
        "## Files",
        "",
    ]

    for name, dest_name in ROOT_DOC_DEST_MAP.items():
        source = ROOT / name
        title = read_title(source) or humanize(name)
        lines.append(f"- [{title}]({dest_name})")

    lines.append("")

    destination_rel = PROJECT_REPO_DIR / "index.md"
    write_file(destination_rel, "\n".join(lines) + "\n", "/README.md")


def main() -> None:
    dest_dir = DOCS_DIR / PROJECT_REPO_DIR
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    write_project_docs()
    write_index()


if __name__ == "__main__":
    main()
