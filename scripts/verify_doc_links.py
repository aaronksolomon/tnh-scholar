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
        raw_text = md_file.read_text(encoding="utf-8")
        text = strip_code(raw_text)
        replacements: dict[str, str] = {}
        for match in LINK_PATTERN.finditer(text):
            label, target = match.group(1), match.group(2)
            if is_external(target) or target.startswith("#"):
                continue

            target_no_fragment = normalize_target(target)
            if not target_no_fragment:
                continue

            # Accept repo-root mirrors as-is; they are synced docs.
            if "project/repo-root/" in target_no_fragment:
                continue

            # Only validate markdown targets; skip other extensions (e.g., evidence .txt).
            suffix = Path(target_no_fragment).suffix
            if suffix and suffix.lower() != ".md":
                continue

            total_links += 1

            target_is_absolute = target.startswith("/")
            rel_candidate = (md_file.parent / target_no_fragment).resolve()
            abs_candidate = docs_root / target_no_fragment

            # Absolute links that resolve are fine as-is.
            if target_is_absolute and abs_candidate.is_file():
                continue

            # Relative links that resolve should be normalized to absolute.
            if not target_is_absolute and docs_root in rel_candidate.parents and rel_candidate.is_file():
                rel_to_docs = rel_candidate.relative_to(docs_root).as_posix()
                fixed = f"/{rel_to_docs}"
                issues.append(
                    LinkIssue(
                        file=md_file,
                        original=target,
                        fixed=fixed,
                        reason="normalize to absolute",
                    )
                )
                replacements[target] = fixed
                auto_fix_candidates += 1
                auto_fix_files.add(md_file)
                continue

            # Normalize any docs/ prefix for lookup.
            if target_no_fragment.startswith("docs/"):
                target_no_fragment = target_no_fragment[len("docs/") :]

            basename = Path(target_no_fragment).name
            candidates = basename_index.get(basename, [])

            if len(candidates) == 1:
                candidate_rel = candidates[0].relative_to(docs_root).as_posix()
                fixed = f"/{candidate_rel}"
                issues.append(
                    LinkIssue(
                        file=md_file,
                        original=target,
                        fixed=fixed,
                        reason="auto-fix (unique filename match)",
                    )
                )
                replacements[target] = fixed
                auto_fix_candidates += 1
                auto_fix_files.add(md_file)
            elif len(candidates) > 1:
                issue = LinkIssue(
                    file=md_file,
                    original=target,
                    fixed=None,
                    reason=f"ambiguous ({len(candidates)} matches for {basename})",
                )
                issues.append(issue)
                if debug:
                    print(f"[debug] ambiguous link in {md_file}: {target} -> candidates={len(candidates)}")
            else:
                issue = LinkIssue(
                    file=md_file,
                    original=target,
                    fixed=None,
                    reason="no matching filename in docs/",
                )
                issues.append(issue)
                if debug:
                    print(f"[debug] missing link in {md_file}: {target}")

        if apply and replacements:
            new_text = replace_links(raw_text, replacements)
            if new_text != raw_text:
                md_file.write_text(new_text, encoding="utf-8")
                modified_files.append(md_file)
                fixed_links_count += len(replacements)
                if verbose:
                    print(f"Updated {md_file} ({len(replacements)} replacements)")
    return issues, modified_files, total_links, auto_fix_candidates, fixed_links_count, auto_fix_files


def main(argv: Iterable[str] | None = None) -> int:
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
    parser.add_argument(
        "--verbose", action="store_true", help="Print per-file replacement details"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print debugging info for flagged links"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when issues are found (default: warn-only).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    docs_root = args.docs_root.resolve()
    if not docs_root.is_dir():
        print(f"Docs root not found: {docs_root}", file=sys.stderr)
        return 2

    issues, modified, total_links, auto_fix_candidates, fixed_count, auto_fix_files = find_link_issues(
        docs_root, apply=args.apply, verbose=args.verbose, debug=args.debug
    )

    auto_fixes = [iss for iss in issues if iss.fixed]
    flagged = [iss for iss in issues if iss.fixed is None]

    if args.apply:
        print(f"Links inspected: {total_links}")
        print(f"Links fixed: {fixed_count}")
        print(f"Files updated: {len(modified)}")
        if modified:
            print("Updated files:")
            for path in sorted(modified):
                try:
                    rel_path = path.relative_to(docs_root)
                except ValueError:
                    rel_path = path
                print(f"- {rel_path}")
    else:
        print(f"Links inspected: {total_links}")
        print(f"Links needing fix: {auto_fix_candidates}")
        if auto_fix_files:
            print("Files with auto-fixes pending:")
            for path in sorted(auto_fix_files):
                print(f"- {path}")
        print(f"Links needing manual review: {len(flagged)}")

    if flagged:
        print("\nManual review needed:")
        for iss in flagged:
            print(f"- {iss.file}: '{iss.original}' -> {iss.reason}")

    # Fail only in strict mode. Otherwise warn-only so CI can proceed.
    if flagged or (auto_fixes and not args.apply):
        if auto_fixes and not args.apply:
            print("\nRun with --apply to rewrite unambiguous markdown links.")
        return 1 if args.strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
