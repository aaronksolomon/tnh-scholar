"""Run tnh-gen separately on blank-line-delimited paragraphs, retaining artifacts."""

import argparse
import difflib
import json
import re
import subprocess
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import tiktoken


@dataclass(frozen=True)
class GrammarConfig:
    """Configuration for one retained grammar run."""

    source: Path
    run_dir: Path
    prompt_dir: Path
    workers: int = 3
    prompt: str = "sr-d-paragraph-grammar"
    model: str = "gpt-5.6-sol"
    reasoning: str = "low"
    max_tokens: int = 8192
    requests_per_minute: int = 12
    tokens_per_minute: int = 60000


class WorkflowRateLimiter:
    """Share paced request starts and token reservations across worker threads."""

    def __init__(self, config: GrammarConfig) -> None:
        self.config = config
        self._lock = Lock()
        self._reservations: deque[tuple[float, int]] = deque()
        self._next_start = 0.0

    def acquire(self, tokens: int) -> None:
        """Wait for a logical CLI request slot; SDK retries remain internal."""
        if tokens > self.config.tokens_per_minute:
            raise ValueError("One request exceeds the configured token-per-minute budget.")
        with self._lock:
            self._wait_for_capacity(tokens)
            now = time.monotonic()
            self._reservations.append((now, tokens))
            self._next_start = now + 60 / self.config.requests_per_minute

    def _wait_for_capacity(self, tokens: int) -> None:
        """Expire sliding-window reservations and pace starts to avoid bursts."""
        while True:
            now = time.monotonic()
            while self._reservations and self._reservations[0][0] <= now - 60:
                self._reservations.popleft()
            delay = max(0.0, self._next_start - now)
            if sum(size for _, size in self._reservations) + tokens > self.config.tokens_per_minute:
                delay = max(delay, self._reservations[0][0] + 60 - now)
            if delay <= 0:
                return
            time.sleep(delay)


def split_paragraphs(text: str) -> list[str]:
    """Split on blank lines, keeping wrapped lines within each paragraph."""
    return [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]


def validate_paragraph(text: str) -> str:
    """Reject empty, wrapped, or multiple-paragraph model output."""
    parts = split_paragraphs(text)
    if len(parts) != 1 or parts[0].startswith(("```", "---", "#")):
        raise ValueError("Expected exactly one plain-text paragraph.")
    return parts[0]


def cli_command(config: GrammarConfig, folder: Path) -> list[str]:
    """Build a bounded tnh-gen CLI request for one paragraph."""
    return [
        "poetry",
        "run",
        "tnh-gen",
        "--api",
        "--prompt-dir",
        str(config.prompt_dir),
        "run",
        "--prompt",
        config.prompt,
        "--model",
        config.model,
        "--input-file",
        str(folder / "source.txt"),
        "--reasoning",
        config.reasoning,
        "--max-tokens",
        str(config.max_tokens),
        "--no-provenance",
        "--output-file",
        str(folder / "generated.txt"),
    ]


def save_diff(folder: Path, source: str, corrected: str) -> None:
    """Save a word-level unified diff for review."""
    lines = difflib.unified_diff(
        [word + "\n" for word in source.split()],
        [word + "\n" for word in corrected.split()],
        fromfile="source.txt",
        tofile="corrected.txt",
        n=8,
    )
    (folder / "changes.diff").write_text("".join(lines), encoding="utf-8")


def process_paragraph(config: GrammarConfig, limiter: WorkflowRateLimiter, number: int, source: str) -> str:
    """Process and retain one paragraph without changing its source file."""
    folder = config.run_dir / f"paragraph-{number:03d}"
    folder.mkdir()
    (folder / "source.txt").write_text(source + "\n", encoding="utf-8")
    command = cli_command(config, folder)
    (folder / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    encoding = tiktoken.get_encoding("o200k_base")
    prompt = (config.run_dir / "prompt.md").read_text(encoding="utf-8")
    limiter.acquire(len(encoding.encode(source + prompt)) + config.max_tokens)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    (folder / "response.json").write_text(result.stdout, encoding="utf-8")
    (folder / "stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Paragraph {number} failed; inspect {folder}.")
    corrected = validate_paragraph((folder / "generated.txt").read_text(encoding="utf-8"))
    (folder / "corrected.txt").write_text(corrected + "\n", encoding="utf-8")
    save_diff(folder, source, corrected)
    return corrected


def collect_results(config: GrammarConfig, paragraphs: list[str]) -> list[str]:
    """Collect independent paragraph calls in source order; retain any failures."""
    results = [""] * len(paragraphs)
    failures: list[str] = []
    limiter = WorkflowRateLimiter(config)
    with ThreadPoolExecutor(max_workers=config.workers) as executor:
        pending = {
            executor.submit(process_paragraph, config, limiter, number, source): number
            for number, source in enumerate(paragraphs, 1)
        }
        for future in as_completed(pending):
            number = pending[future]
            try:
                results[number - 1] = future.result()
                print(f"Completed paragraph {number}/{len(paragraphs)}", flush=True)
            except Exception as error:
                failures.append(str(error))
    if failures:
        (config.run_dir / "failures.txt").write_text("\n".join(failures), encoding="utf-8")
        raise RuntimeError("Run incomplete; retained intermediates, no combined output.")
    return results


def paragraph_report(number: int, source: str, corrected: str) -> str:
    """Report per-paragraph word counts and edit size, without claiming semantic proof."""
    before, after = source.split(), corrected.split()
    matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
    removed = sum(j - i for tag, i, j, _, _ in matcher.get_opcodes() if tag != "equal")
    return (
        f"Paragraph {number:03d}: {len(before)} -> {len(after)} words; "
        f"{removed} source tokens edited/deleted; net {len(after) - len(before):+d}."
    )


def write_outputs(config: GrammarConfig, sources: list[str], results: list[str]) -> None:
    """Write ordered candidate output and a reviewable side-by-side comparison."""
    (config.run_dir / "grammar.txt").write_text("\n\n".join(results) + "\n", encoding="utf-8")
    comparison = difflib.HtmlDiff(wrapcolumn=90).make_file(
        sources,
        results,
        fromdesc="Stage 1: verbatim paragraphs",
        todesc="Stage 2: grammar corrections",
        charset="utf-8",
    )
    (config.run_dir / "comparison.html").write_text(comparison, encoding="utf-8")
    report = ["Grammar candidates: review edits for meaning and omissions."]
    report.extend(paragraph_report(n, a, b) for n, (a, b) in enumerate(zip(sources, results), 1))
    (config.run_dir / "review.txt").write_text("\n".join(report) + "\n", encoding="utf-8")


def run(config: GrammarConfig) -> None:
    """Create a fresh retained run and process its paragraph snapshot."""
    source = config.source.read_text(encoding="utf-8")
    paragraphs = split_paragraphs(source)
    if not paragraphs:
        raise ValueError("Source transcript is empty.")
    config.run_dir.mkdir(parents=True, exist_ok=False)
    (config.run_dir / "stage-1.txt").write_text(source, encoding="utf-8")
    prompt = config.prompt_dir / f"{config.prompt}.md"
    (config.run_dir / "prompt.md").write_text(prompt.read_text(), encoding="utf-8")
    results = collect_results(config, paragraphs)
    write_outputs(config, paragraphs, results)
    print(f"Retained {len(results)} paragraphs and comparisons in {config.run_dir}", flush=True)


def main() -> None:
    """Parse explicit local paths for a fresh workflow run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("run_dir", type=Path, help="New directory; existing runs are never overwritten.")
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=3)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning", default="low")
    parser.add_argument("--requests-per-minute", type=int, default=12)
    parser.add_argument("--tokens-per-minute", type=int, default=60000)
    args = parser.parse_args()
    if args.requests_per_minute <= 0 or args.tokens_per_minute <= 0:
        parser.error("Rate limits must be positive.")
    prompt_dir = Path(__file__).resolve().parent / "prompts"
    run(
        GrammarConfig(
            source=args.source.resolve(),
            run_dir=args.run_dir.resolve(),
            prompt_dir=prompt_dir,
            workers=args.workers,
            model=args.model,
            reasoning=args.reasoning,
            requests_per_minute=args.requests_per_minute,
            tokens_per_minute=args.tokens_per_minute,
        )
    )


if __name__ == "__main__":
    main()
