#!/usr/bin/env python3
"""
Convert relative markdown links to absolute paths for MkDocs.

MkDocs 1.6+ supports absolute links with validation.links.absolute_links: relative_to_docs
This script converts patterns like `[text](../foo/bar.md)` to `[text](/foo/bar.md)`
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


def find_relative_links(content: str) -> List[Tuple[str, str]]:
    """
    Find all relative markdown links in content.

    Returns list of (full_match, relative_path) tuples.
    """
    # Pattern to match markdown links with relative paths
    # Matches [text](../path) or [text](./path) but not [text](http://...) or [text](/absolute)
    pattern = r'\[([^\]]+)\]\((\.\./[^\)]+|\.\/[^\)]+)\)'
    matches = re.findall(pattern, content)
    return [(f'[{text}]({path})', path) for text, path in matches]


def resolve_relative_path(file_path: Path, relative_path: str, docs_root: Path) -> str:
    """
    Convert a relative path to an absolute path from docs/ root.

    Args:
        file_path: Path to the markdown file containing the link
        relative_path: The relative path from the link (e.g., "../foo/bar.md")
        docs_root: Path to the docs/ directory

    Returns:
        Absolute path from docs/ root (e.g., "/foo/bar.md")
    """
    # Get the directory containing the markdown file
    file_dir = file_path.parent

    # Resolve the relative path from the file's directory
    target_path = (file_dir / relative_path).resolve()

    # Make it relative to docs/ directory
    try:
        relative_to_docs = target_path.relative_to(docs_root)
        # Convert to absolute path notation (starting with /)
        absolute_path = '/' + str(relative_to_docs).replace('\\', '/')
        return absolute_path
    except ValueError:
        # Path is outside docs/ directory - leave it as is
        return relative_path


def convert_links_in_file(file_path: Path, docs_root: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Convert all relative links in a file to absolute paths.

    Returns:
        (count_of_conversions, list_of_conversions)
    """
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    conversions = []

    # Find all relative links
    relative_links = find_relative_links(content)

    for full_match, relative_path in relative_links:
        # Skip external links
        if relative_path.startswith('http://') or relative_path.startswith('https://'):
            continue

        # Convert to absolute path
        absolute_path = resolve_relative_path(file_path, relative_path, docs_root)

        # Extract the link text
        text_match = re.match(r'\[([^\]]+)\]', full_match)
        if text_match:
            link_text = text_match.group(1)
            new_link = f'[{link_text}]({absolute_path})'

            # Replace in content
            content = content.replace(full_match, new_link)

            # Track conversion
            conversion_msg = f"  {relative_path} → {absolute_path}"
            conversions.append(conversion_msg)

    # Write back if content changed and not dry run
    if content != original_content and not dry_run:
        file_path.write_text(content, encoding='utf-8')

    return len(conversions), conversions


def main():
    """Main conversion process."""
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_root = project_root / 'docs'

    if not docs_root.exists():
        print(f"Error: docs/ directory not found at {docs_root}")
        return 1

    # Find all markdown files with relative links
    print("Scanning for markdown files with relative links...")

    all_md_files = list(docs_root.rglob('*.md'))
    files_to_process = []

    for md_file in all_md_files:
        content = md_file.read_text(encoding='utf-8')
        if '](..' in content or '](./' in content:
            # Has relative links
            files_to_process.append(md_file)

    print(f"Found {len(files_to_process)} files with relative links\n")

    # Process each file
    total_conversions = 0
    files_modified = 0

    for file_path in files_to_process:
        relative_path = file_path.relative_to(docs_root)
        count, conversions = convert_links_in_file(file_path, docs_root, dry_run=False)

        if count > 0:
            print(f"{relative_path} ({count} links):")
            for conversion in conversions:
                print(conversion)
            print()

            total_conversions += count
            files_modified += 1

    # Summary
    print("=" * 80)
    print("CONVERSION SUMMARY")
    print("=" * 80)
    print(f"Total files modified: {files_modified}")
    print(f"Total links converted: {total_conversions}")
    print()

    # Test with mkdocs build
    print("Testing with mkdocs build...")
    import subprocess
    try:
        result = subprocess.run(
            ['mkdocs', 'build', '--strict'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✓ mkdocs build succeeded!")
        else:
            print("✗ mkdocs build failed:")
            print(result.stderr)
            return 1
    except FileNotFoundError:
        print("⚠ mkdocs not found - skipping build test")
    except subprocess.TimeoutExpired:
        print("⚠ mkdocs build timed out")

    return 0


if __name__ == '__main__':
    exit(main())
