#!/usr/bin/env python3
"""Prepare README.md for PyPI by stripping YAML frontmatter.

This script should be run before 'poetry build' to ensure the README
displays correctly on PyPI without YAML frontmatter appearing as plain text.

Usage:
    python scripts/prepare_pypi_readme.py        # Strip frontmatter
    python scripts/prepare_pypi_readme.py --restore  # Restore original
"""

import argparse
import re
import shutil
from pathlib import Path


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content.

    Args:
        content: The markdown content potentially containing frontmatter

    Returns:
        Content with frontmatter removed
    """
    # Match YAML frontmatter: --- at start, content, then ---
    frontmatter_pattern = r'^---\s*\n.*?\n---\s*\n'

    # Remove frontmatter if it exists at the start of the file
    cleaned = re.sub(frontmatter_pattern, '', content, count=1, flags=re.DOTALL)

    return cleaned


def main():
    """Strip frontmatter from README.md or restore backup."""
    parser = argparse.ArgumentParser(description="Prepare README for PyPI distribution")
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore README from backup instead of stripping frontmatter",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    readme_path = project_root / "README.md"
    backup_path = project_root / "README.md.bak"

    if args.restore:
        # Restore from backup
        if not backup_path.exists():
            print(f"⚠ No backup found at {backup_path}")
            return 1

        shutil.copy2(backup_path, readme_path)
        backup_path.unlink()
        print(f"✓ Restored README.md from backup")
        return 0

    # Strip frontmatter
    if not readme_path.exists():
        print(f"✗ README.md not found at {readme_path}")
        return 1

    # Create backup
    shutil.copy2(readme_path, backup_path)
    print(f"✓ Backed up README.md to {backup_path}")

    # Read original README
    content = readme_path.read_text(encoding="utf-8")

    # Strip frontmatter
    cleaned_content = strip_frontmatter(content)

    # Write cleaned version
    readme_path.write_text(cleaned_content, encoding="utf-8")

    # Check if anything was actually removed
    if len(content) == len(cleaned_content):
        print(f"ℹ No frontmatter found in README.md")
    else:
        removed_bytes = len(content) - len(cleaned_content)
        print(f"✓ Stripped {removed_bytes} bytes of frontmatter from README.md")

    print(f"\n📦 README.md is ready for PyPI build")
    print(f"💡 Run 'python scripts/prepare_pypi_readme.py --restore' to restore original")

    return 0


if __name__ == "__main__":
    exit(main())
