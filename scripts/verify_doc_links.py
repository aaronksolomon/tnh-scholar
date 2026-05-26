#!/usr/bin/env python3
"""Scan markdown docs for broken links and optionally auto-fix obvious cases.

Workflow:
1) Find links in all .md files under docs/ (inline markdown links only).
2) If target exists, skip.
3) If missing, look for a single docs/ match with the same filename.
   - If exactly one match, rewrite to absolute path ("/<path>") when --apply.
   - If multiple or none, report as ambiguous/missing.
4) Emit a summary of applied or suggested fixes.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


@dataclass
class LinkIssue:
    file: Path
    original: str
    fixed: str | None
    reason: str


def iter_markdown_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        if "archive" in path.parts:
            continue
        if is_auto_generated(path):
            continue
        yield path


def is_auto_generated(path: Path) -> bool:
    """Return True if file declares auto_generated: true in front matter."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    if not lines or lines[0].strip() != "---":
        return False
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            block = "\n".join(lines[1:idx])
            return "auto_generated: true" in block.lower()
    return False


def strip_code(text: str) -> str:
    """Remove fenced and inline code segments to avoid inspecting links inside code."""
    # Remove fenced code blocks (``` ... ```), non-greedy across lines.
    without_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove inline code spans using backticks.
    return re.sub(r"`[^`]+`", "", without_fences)


def build_basename_index(root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = defaultdict(list)
    for path in iter_markdown_files(root):
        index[path.name].append(path)
    return index


def is_external(link: str) -> bool:
    return any(link.startswith(prefix) for prefix in ("http://", "https://", "mailto:"))


def normalize_target(link: str) -> str:
    """Drop fragments and leading slashes; keep posix style."""
    link = link.split("#", 1)[0]
    if link.startswith("/"):
        link = link[1:]
    return link


def replace_links(text: str, replacements: dict[str, str]) -> str:
    """Replace exact link targets in markdown link syntax."""

    def repl(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        new_target = replacements.get(target)
        return f"[{label}]({new_target})" if new_target else match.group(0)

    return LINK_PATTERN.sub(repl, text)


def classify_target(
    md_file: Path,
    target: str,
    docs_root: Path,
) -> tuple[str | None, LinkIssue | None]:
    """Return a normalized lookup target or an immediate issue."""
    target_no_fragment = normalize_target(target)
    if not target_no_fragment:
        return None, None
    if "project/repo-root/" in target_no_fragment:
        return None, None

    suffix = Path(target_no_fragment).suffix
    if suffix and suffix.lower() != ".md":
        return None, None

    target_is_absolute = target.startswith("/")
    rel_candidate = (md_file.parent / target_no_fragment).resolve()
    abs_candidate = docs_root / target_no_fragment
    if target_is_absolute and abs_candidate.is_file():
        return None, None

    if not target_is_absolute and docs_root in rel_candidate.parents and rel_candidate.is_file():
        rel_to_docs = rel_candidate.relative_to(docs_root).as_posix()
        fixed = f"/{rel_to_docs}"
        return None, LinkIssue(
            file=md_file,
            original=target,
            fixed=fixed,
            reason="normalize to absolute",
        )

    normalized_target = target_no_fragment
    if normalized_target.startswith("docs/"):
        normalized_target = normalized_target[len("docs/") :]
    return normalized_target, None


def resolve_missing_target(
    md_file: Path,
    target: str,
    normalized_target: str,
    basename_index: dict[str, list[Path]],
    docs_root: Path,
) -> LinkIssue:
    """Resolve a missing markdown target against basename index."""
    basename = Path(normalized_target).name
    candidates = basename_index.get(basename, [])
    if len(candidates) == 1:
        candidate_rel = candidates[0].relative_to(docs_root).as_posix()
        return LinkIssue(
            file=md_file,
            original=target,
            fixed=f"/{candidate_rel}",
            reason="auto-fix (unique filename match)",
        )
    if len(candidates) > 1:
        return LinkIssue(
            file=md_file,
            original=target,
            fixed=None,
            reason=f"ambiguous ({len(candidates)} matches for {basename})",
        )
    return LinkIssue(
        file=md_file,
        original=target,
        fixed=None,
        reason="no matching filename in docs/",
    )


def inspect_file_links(
    md_file: Path,
    docs_root: Path,
    basename_index: dict[str, list[Path]],
    debug: bool,
) -> tuple[list[LinkIssue], dict[str, str], int]:
    """Inspect one markdown file and return issues, replacements, and link count."""
    raw_text = md_file.read_text(encoding="utf-8")
    text = strip_code(raw_text)
    issues: list[LinkIssue] = []
    replacements: dict[str, str] = {}
    total_links = 0

    for match in LINK_PATTERN.finditer(text):
        target = match.group(2)
        if is_external(target) or target.startswith("#"):
            continue

        total_links += 1
        normalized_target, immediate_issue = classify_target(md_file, target, docs_root)
        if normalized_target is None and immediate_issue is None:
            total_links -= 1
            continue
        if immediate_issue is not None:
            issues.append(immediate_issue)
            if immediate_issue.fixed:
                replacements[target] = immediate_issue.fixed
            continue

        issue = resolve_missing_target(md_file, target, normalized_target, basename_index, docs_root)
        issues.append(issue)
        if issue.fixed:
            replacements[target] = issue.fixed
            continue
        if debug:
            print(f"[debug] unresolved link in {md_file}: {target} -> {issue.reason}")

    return issues, replacements, total_links


def find_link_issues(
    docs_root: Path, apply: bool, verbose: bool, debug: bool = False
) -> tuple[list[LinkIssue], list[Path], int, int, int, set[Path]]:
    basename_index = build_basename_index(docs_root)
    modified_files: list[Path] = []
    issues: list[LinkIssue] = []
    total_links = 0
    auto_fix_candidates = 0
    fixed_links_count = 0
    auto_fix_files: set[Path] = set()

    for md_file in iter_markdown_files(docs_root):
        file_issues, replacements, link_count = inspect_file_links(md_file, docs_root, basename_index, debug)
        issues.extend(file_issues)
        total_links += link_count
        for issue in file_issues:
            if issue.fixed:
                auto_fix_candidates += 1
                auto_fix_files.add(md_file)

        if apply and replacements:
            raw_text = md_file.read_text(encoding="utf-8")
            new_text = replace_links(raw_text, replacements)
            if new_text != raw_text:
                md_file.write_text(new_text, encoding="utf-8")
                modified_files.append(md_file)
                fixed_links_count += len(replacements)
                if verbose:
                    print(f"Updated {md_file} ({len(replacements)} replacements)")
    return issues, modified_files, total_links, auto_fix_candidates, fixed_links_count, auto_fix_files


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=Path("docs"),
        help="Root directory containing markdown docs (default: docs)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply auto-fixes when there is a single unambiguous match, "
        "and normalize resolvable relative links to absolute.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print per-file replacement details")
    parser.add_argument("--debug", action="store_true", help="Print debugging info for flagged links")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when issues are found (default: warn-only).",
    )
    return parser


def print_apply_summary(
    *,
    docs_root: Path,
    modified: list[Path],
    total_links: int,
    fixed_count: int,
) -> None:
    """Print summary for apply mode."""
    print(f"Links inspected: {total_links}")
    print(f"Links fixed: {fixed_count}")
    print(f"Files updated: {len(modified)}")
    if not modified:
        return
    print("Updated files:")
    for path in sorted(modified):
        try:
            rel_path = path.relative_to(docs_root)
        except ValueError:
            rel_path = path
        print(f"- {rel_path}")


def print_check_summary(
    *,
    auto_fix_candidates: int,
    auto_fix_files: set[Path],
    flagged: list[LinkIssue],
    total_links: int,
) -> None:
    """Print summary for check mode."""
    print(f"Links inspected: {total_links}")
    print(f"Links needing fix: {auto_fix_candidates}")
    if auto_fix_files:
        print("Files with auto-fixes pending:")
        for path in sorted(auto_fix_files):
            print(f"- {path}")
    print(f"Links needing manual review: {len(flagged)}")


def print_manual_review(flagged: list[LinkIssue]) -> None:
    """Print manual review details."""
    if not flagged:
        return
    print("\nManual review needed:")
    for iss in flagged:
        print(f"- {iss.file}: '{iss.original}' -> {iss.reason}")


def report_results(
    *,
    args: argparse.Namespace,
    docs_root: Path,
    issues: list[LinkIssue],
    modified: list[Path],
    total_links: int,
    auto_fix_candidates: int,
    fixed_count: int,
    auto_fix_files: set[Path],
) -> int:
    """Print summary and return exit code."""
    auto_fixes = [iss for iss in issues if iss.fixed]
    flagged = [iss for iss in issues if iss.fixed is None]

    if args.apply:
        print_apply_summary(
            docs_root=docs_root,
            modified=modified,
            total_links=total_links,
            fixed_count=fixed_count,
        )
    else:
        print_check_summary(
            auto_fix_candidates=auto_fix_candidates,
            auto_fix_files=auto_fix_files,
            flagged=flagged,
            total_links=total_links,
        )

    print_manual_review(flagged)

    if flagged or (auto_fixes and not args.apply):
        if auto_fixes and not args.apply:
            print("\nRun with --apply to rewrite unambiguous markdown links.")
        return 1 if args.strict else 0
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    docs_root = args.docs_root.resolve()
    if not docs_root.is_dir():
        print(f"Docs root not found: {docs_root}", file=sys.stderr)
        return 2

    issues, modified, total_links, auto_fix_candidates, fixed_count, auto_fix_files = find_link_issues(
        docs_root, apply=args.apply, verbose=args.verbose, debug=args.debug
    )

    return report_results(
        args=args,
        docs_root=docs_root,
        issues=issues,
        modified=modified,
        total_links=total_links,
        auto_fix_candidates=auto_fix_candidates,
        fixed_count=fixed_count,
        auto_fix_files=auto_fix_files,
    )


if __name__ == "__main__":
    sys.exit(main())
