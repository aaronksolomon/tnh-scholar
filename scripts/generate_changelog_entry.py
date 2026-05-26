#!/usr/bin/env python3
"""Generate CHANGELOG entry from git commits since last tag.

This script analyzes git commits since the last tag and generates a draft
CHANGELOG.md entry categorized by commit type (feat, fix, docs, etc.).

Usage:
    python scripts/generate_changelog_entry.py
    make changelog-draft
"""

import subprocess
import sys
from datetime import date


def initialize_categories() -> dict[str, list[str]]:
    """Return empty changelog categories."""
    return {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Documentation": [],
        "Infrastructure": [],
        "Other": [],
    }


def category_from_prefix(commit: str) -> str | None:
    """Return category for conventional commit prefixes."""
    if commit.startswith(("feat:", "add:")):
        return "Added"
    if commit.startswith("fix:"):
        return "Fixed"
    if commit.startswith("docs:"):
        return "Documentation"
    if commit.startswith(("chore:", "build:", "ci:")):
        return "Infrastructure"
    if commit.startswith(("refactor:", "perf:")):
        return "Changed"
    return None


def category_from_content(commit: str) -> str:
    """Return best-effort category for non-conventional commits."""
    commit_lower = commit.lower()
    if any(word in commit_lower for word in ["add", "new", "implement", "create"]):
        return "Added"
    if any(word in commit_lower for word in ["fix", "resolve", "correct"]):
        return "Fixed"
    if any(word in commit_lower for word in ["update", "change", "refactor"]):
        return "Changed"
    if any(word in commit_lower for word in ["doc", "readme", "changelog"]):
        return "Documentation"
    return "Other"


def get_last_tag():
    """Get the most recent git tag."""
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def get_commits_since_tag(tag):
    """Get commit messages since the given tag."""
    cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%s"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    commits = result.stdout.strip().split("\n") if result.stdout.strip() else []
    return [c for c in commits if c]  # Filter empty strings


def categorize_commits(commits):
    """Categorize commits by type (feat, fix, docs, chore, etc.)."""
    categories = initialize_categories()

    for commit in commits:
        if commit.startswith("Merge "):
            continue

        category = category_from_prefix(commit) or category_from_content(commit)
        categories[category].append(commit)

    return {k: v for k, v in categories.items() if v}


def format_changelog_entry(version, categories):
    """Format the changelog entry in standard format."""
    today = date.today().isoformat()

    output = [f"## [{version}] - {today}\n"]

    for category, commits in categories.items():
        if commits:
            output.append(f"### {category}\n")
            for commit in commits:
                # Remove conventional commit prefix for cleaner output
                if ":" in commit:
                    msg = commit.split(":", 1)[-1].strip()
                else:
                    msg = commit.strip()

                # Capitalize first letter if not already
                if msg and msg[0].islower():
                    msg = msg[0].upper() + msg[1:]

                output.append(f"- {msg}")
            output.append("")

    return "\n".join(output)


def main():
    """Main entry point."""
    last_tag = get_last_tag()
    if not last_tag:
        print("No previous tag found. Cannot generate changelog.", file=sys.stderr)
        print(
            "\nThis is likely your first release. Write the changelog manually.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Get current version from pyproject.toml using poetry
    result = subprocess.run(
        ["poetry", "version", "-s"],
        capture_output=True,
        text=True,
        check=True,
    )
    current_version = result.stdout.strip()

    commits = get_commits_since_tag(last_tag)
    if not commits:
        print(f"No commits since {last_tag}", file=sys.stderr)
        print(
            "\nNo changes to document. You may want to skip this release.",
            file=sys.stderr,
        )
        sys.exit(0)

    categories = categorize_commits(commits)
    if not categories:
        print(f"No categorizable commits since {last_tag}", file=sys.stderr)
        print(
            "\nAll commits appear to be merges. Write changelog manually if needed.",
            file=sys.stderr,
        )
        sys.exit(0)

    changelog_entry = format_changelog_entry(current_version, categories)

    print(changelog_entry)
    print("\n" + "=" * 60)
    print(f"📝 Draft CHANGELOG entry for v{current_version}")
    print(f"Based on {len(commits)} commits since {last_tag}")
    print("=" * 60)


if __name__ == "__main__":
    main()
