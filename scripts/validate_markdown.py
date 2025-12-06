#!/usr/bin/env python3
"""Validate markdown files against TNH Scholar documentation standards.

This script validates that all markdown files in the docs/ directory comply with
the standards defined in docs/docs-ops/markdown-standards.md.

Checks performed:
- Frontmatter exists with all required fields (title, description, owner, author,
  status, created)
- Title in frontmatter exactly matches the # heading in the document
- First paragraph exists after the title heading (description)

Usage:
    # Run validation manually
    poetry run python scripts/validate_markdown.py

    # Run via make target (recommended)
    make docs-validate

The script is automatically run during docs-generate and docs-build.
Exit code 1 indicates validation issues, but this is treated as a warning
(non-fatal) in the build process.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, NamedTuple

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

EXCLUDED_DIRS = {
    ".git",
    ".github",
    "site",
    "build",
    "dist",
    "__pycache__",
}

# Required frontmatter fields
REQUIRED_FIELDS = ["title", "description", "owner", "author", "status", "created"]

# Directories that may use specialized frontmatter (e.g., prompt templates)
SPECIAL_FRONTMATTER_DIRS = {"patterns", "prompt-templates"}


class ValidationIssue(NamedTuple):
    """Represents a validation issue in a markdown file."""
    file_path: Path
    issue_type: str
    message: str


def parse_frontmatter(path: Path) -> tuple[Dict, int]:
    """Return (frontmatter dict, line number where content starts)."""
    try:
        text = path.read_text()
    except FileNotFoundError:
        return {}, 0

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0

    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            try:
                fm = yaml.safe_load("\n".join(lines[1:idx])) or {}
                return fm, idx + 1
            except Exception:
                return {}, 0
    return {}, 0


def get_first_heading(lines: List[str]) -> tuple[str, int] | None:
    """Return (heading text, line number) of first # heading, or None."""
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            return line[2:].strip(), idx
    return None


def get_first_paragraph(lines: List[str], after_line: int) -> str:
    """Return first non-empty paragraph after the given line number."""
    in_paragraph = False
    paragraph_lines = []

    for idx in range(after_line + 1, len(lines)):
        line = lines[idx].strip()

        # Skip empty lines before paragraph starts
        if not line and not in_paragraph:
            continue

        # Skip HTML comments
        if line.startswith("<!--"):
            continue

        # Stop at next heading or code block
        if line.startswith("#") or line.startswith("```"):
            break

        # Empty line ends the paragraph
        if not line and in_paragraph:
            break

        # Accumulate paragraph text
        if line:
            in_paragraph = True
            paragraph_lines.append(line)

    return " ".join(paragraph_lines)


def is_special_frontmatter_file(path: Path) -> bool:
    """Check if file is in a directory with specialized frontmatter."""
    parts = path.relative_to(DOCS_ROOT).parts
    return any(part in SPECIAL_FRONTMATTER_DIRS for part in parts)


def validate_file(path: Path) -> List[ValidationIssue]:
    """Validate a single markdown file against standards."""
    issues = []
    rel_path = path.relative_to(DOCS_ROOT)

    # Skip files with specialized frontmatter schemas
    if is_special_frontmatter_file(path):
        return issues

    # Parse frontmatter
    frontmatter, content_start = parse_frontmatter(path)

    # Check frontmatter exists
    if not frontmatter:
        issues.append(ValidationIssue(
            rel_path,
            "missing_frontmatter",
            "File is missing YAML frontmatter"
        ))
        return issues  # Can't validate further without frontmatter

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            issues.append(ValidationIssue(
                rel_path,
                "missing_field",
                f"Frontmatter missing required field: {field}"
            ))

    # Read content lines
    try:
        lines = path.read_text().splitlines()
    except Exception as e:
        issues.append(ValidationIssue(
            rel_path,
            "read_error",
            f"Could not read file: {e}"
        ))
        return issues

    # Get content lines (after frontmatter)
    content_lines = lines[content_start:] if content_start else lines

    # Check for first heading
    heading_info = get_first_heading(content_lines)
    if not heading_info:
        issues.append(ValidationIssue(
            rel_path,
            "missing_heading",
            "File is missing a top-level # heading"
        ))
    else:
        heading_text, heading_line_num = heading_info

        # Check title matches heading
        if "title" in frontmatter:
            fm_title = frontmatter["title"].strip()
            if fm_title != heading_text:
                issues.append(ValidationIssue(
                    rel_path,
                    "title_mismatch",
                    f"Title mismatch - frontmatter: '{fm_title}' "
                    f"vs heading: '{heading_text}'"
                ))

        # Check for description paragraph
        first_para = get_first_paragraph(content_lines, heading_line_num)
        if not first_para:
            issues.append(ValidationIssue(
                rel_path,
                "missing_description",
                "File is missing a description paragraph after the title"
            ))

    return issues


def iter_markdown_files() -> List[Path]:
    """Yield all markdown files under docs."""
    files: List[Path] = []
    for path in DOCS_ROOT.rglob("*.md"):
        rel_parts = path.relative_to(DOCS_ROOT).parts
        if not any(part in EXCLUDED_DIRS for part in rel_parts):
            files.append(path)
    return sorted(files)


def main() -> int:
    """Validate all markdown files and report issues."""
    all_issues: List[ValidationIssue] = []

    for md_file in iter_markdown_files():
        issues = validate_file(md_file)
        all_issues.extend(issues)

    if not all_issues:
        print("✓ All markdown files are valid!")
        return 0

    # Group issues by type
    issues_by_type: Dict[str, List[ValidationIssue]] = {}
    for issue in all_issues:
        issues_by_type.setdefault(issue.issue_type, []).append(issue)

    # Report summary
    print(f"\n⚠️  Found {len(all_issues)} validation issue(s) "
          f"in {len(set(i.file_path for i in all_issues))} file(s):\n")

    # Report by type
    for issue_type, issues in sorted(issues_by_type.items()):
        print(f"\n{issue_type.replace('_', ' ').title()} ({len(issues)}):")
        for issue in issues:
            print(f"  • {issue.file_path}: {issue.message}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
