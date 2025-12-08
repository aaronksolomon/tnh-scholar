#!/usr/bin/env python3
"""Report differences between README.md and docs/index.md for review.

Non-blocking check that highlights content drift between the two entry points.
Outputs to docs_sync_report.txt for manual review during project check-ins.
"""
from __future__ import annotations

import re
from datetime import datetime
from difflib import unified_diff
from pathlib import Path

README = Path("README.md")
DOCS_INDEX = Path("docs/index.md")
REPORT_FILE = Path("docs_sync_report.txt")


def extract_sections(content: str) -> dict[str, str]:
    """Extract markdown sections by ## Level 2 heading.

    Returns a dict mapping heading text to section content (excluding the heading itself).
    """
    sections = {}
    lines = content.splitlines()
    current_section = None
    current_content = []

    for line in lines:
        # Match ## headings (but not # or ###)
        if re.match(r'^## [^#]', line):
            # Save previous section
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            # Start new section
            current_section = line[3:].strip()  # Remove "## " prefix
            current_content = []
        elif current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def find_near_matches(title: str, candidates: set[str]) -> list[str]:
    """Find titles that are similar but not exact matches.

    Returns list of candidates that differ only in case, punctuation, or whitespace.
    """
    near_matches = []
    normalized = re.sub(r'[^a-z0-9]', '', title.lower())

    for candidate in candidates:
        candidate_normalized = re.sub(r'[^a-z0-9]', '', candidate.lower())
        if normalized == candidate_normalized and title != candidate:
            near_matches.append(candidate)

    return near_matches


def generate_report() -> str:
    """Generate drift report comparing README and docs/index.md."""
    if not README.exists() or not DOCS_INDEX.exists():
        return "ERROR: README.md or docs/index.md not found"

    readme_content = README.read_text(encoding="utf-8")
    docs_content = DOCS_INDEX.read_text(encoding="utf-8")

    readme_sections = extract_sections(readme_content)
    docs_sections = extract_sections(docs_content)

    report_lines = [
        "=" * 80,
        "README.md ↔ docs/index.md Drift Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
        "",
    ]

    # Track what we've compared
    all_sections = set(readme_sections.keys()) | set(docs_sections.keys())
    matched_sections = set(readme_sections.keys()) & set(docs_sections.keys())
    readme_only = set(readme_sections.keys()) - set(docs_sections.keys())
    docs_only = set(docs_sections.keys()) - set(readme_sections.keys())

    has_diffs = False

    # Compare matched sections
    if matched_sections:
        report_lines.append("Matched Sections (compared):")
        for section in sorted(matched_sections):
            readme_text = readme_sections[section]
            docs_text = docs_sections[section]

            if readme_text == docs_text:
                report_lines.append(f"✓ {section}: IDENTICAL")
            else:
                report_lines.append(f"✗ {section}: DIFFERS")
                report_lines.append("")
                diff = unified_diff(
                    readme_text.splitlines(keepends=True),
                    docs_text.splitlines(keepends=True),
                    fromfile=f"README.md::{section}",
                    tofile=f"docs/index.md::{section}",
                    lineterm=""
                )
                report_lines.extend(diff)
                report_lines.append("")
                has_diffs = True
        report_lines.append("")

    # List sections unique to each file
    if readme_only:
        report_lines.append("Sections only in README.md:")
        for section in sorted(readme_only):
            report_lines.append(f"- {section}")
        report_lines.append("")
        has_diffs = True

    if docs_only:
        report_lines.append("Sections only in docs/index.md:")
        for section in sorted(docs_only):
            report_lines.append(f"- {section}")
        report_lines.append("")
        has_diffs = True

    # Check for near-matches (possible typos)
    near_match_warnings = []
    for readme_section in readme_only:
        matches = find_near_matches(readme_section, docs_only)
        for match in matches:
            near_match_warnings.append(
                f'⚠ "{readme_section}" (README) vs "{match}" (docs/index.md) - possible mismatch'
            )

    if near_match_warnings:
        report_lines.append("Title Mismatches (possible typos):")
        report_lines.extend(near_match_warnings)
        report_lines.append("")
        has_diffs = True

    # Summary
    if has_diffs:
        report_lines.append("⚠ DRIFT DETECTED - Review differences above")
        report_lines.append("This is informational only - no action required unless intentional divergence.")
    else:
        report_lines.append("✓ NO SIGNIFICANT DRIFT DETECTED")

    report_lines.append("")
    report_lines.append("To update: manually edit README.md and/or docs/index.md as appropriate.")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)


def main() -> int:
    """Generate and output drift report (always exits 0)."""
    report = generate_report()

    # Write to file
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Drift report written to {REPORT_FILE}")

    # Also print to console (for CI visibility)
    print("\n" + report)

    # Always exit 0 (non-blocking)
    return 0


if __name__ == "__main__":
    exit(main())
