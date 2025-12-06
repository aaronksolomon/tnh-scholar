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
    categories = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Documentation": [],
        "Infrastructure": [],
        "Other": [],
    }

    for commit in commits:
        # Skip merge commits
        if commit.startswith("Merge "):
            continue

        # Categorize by conventional commit prefix
        if commit.startswith("feat:") or commit.startswith("add:"):
            categories["Added"].append(commit)
        elif commit.startswith("fix:"):
            categories["Fixed"].append(commit)
        elif commit.startswith("docs:"):
            categories["Documentation"].append(commit)
        elif (
            commit.startswith("chore:")
            or commit.startswith("build:")
            or commit.startswith("ci:")
        ):
            categories["Infrastructure"].append(commit)
        elif commit.startswith("refactor:") or commit.startswith("perf:"):
            categories["Changed"].append(commit)
        else:
            # Check for common patterns without conventional commit prefix
            commit_lower = commit.lower()
            if any(
                word in commit_lower
                for word in ["add", "new", "implement", "create"]
            ):
                categories["Added"].append(commit)
            elif any(word in commit_lower for word in ["fix", "resolve", "correct"]):
                categories["Fixed"].append(commit)
            elif any(word in commit_lower for word in ["update", "change", "refactor"]):
                categories["Changed"].append(commit)
            elif any(word in commit_lower for word in ["doc", "readme", "changelog"]):
                categories["Documentation"].append(commit)
            else:
                categories["Other"].append(commit)

    # Remove empty categories
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
        print(
            "No previous tag found. Cannot generate changelog.", file=sys.stderr
        )
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
