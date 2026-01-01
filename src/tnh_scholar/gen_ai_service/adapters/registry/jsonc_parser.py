"""JSONC parsing utilities for registry files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class JsoncParser:
    """JSONC (JSON with Comments) parser."""

    def parse_file(self, path: Path) -> dict:
        """Load and parse JSONC file.

        Args:
            path: Path to JSONC file.

        Returns:
            Parsed dictionary.
        """
        content = path.read_text(encoding="utf-8")
        return self.parse_string(content)

    def parse_string(self, content: str) -> dict:
        """Parse JSONC string into a dictionary.

        Args:
            content: JSONC string content.

        Returns:
            Parsed dictionary.
        """
        try:
            sanitized = self._strip_comments(content)
            sanitized = self._strip_trailing_commas(sanitized)
        except ValueError as exc:
            raise ValueError(f"Invalid JSONC content: {exc}") from exc
        result: dict[str, object] = json.loads(sanitized)
        return result

    def _strip_comments(self, content: str) -> str:
        """Strip // and /* */ comments while preserving JSON strings."""
        state = _ScanState(content)
        result: list[str] = []
        while state.has_more():
            if state.in_string:
                self._consume_string_char(state, result)
                continue
            if self._start_string(state, result):
                continue
            if self._skip_line_comment(state, result):
                continue
            if self._skip_block_comment(state):
                continue
            result.append(state.current())
            state.advance()
        self._ensure_string_closed(state)
        return "".join(result)

    def _strip_trailing_commas(self, content: str) -> str:
        """Remove trailing commas outside of strings."""
        state = _ScanState(content)
        result: list[str] = []
        while state.has_more():
            if state.in_string:
                self._consume_string_char(state, result)
                continue
            if self._start_string(state, result):
                continue
            if state.current() == "," and self._is_trailing_comma(state):
                state.advance()
                continue
            result.append(state.current())
            state.advance()
        self._ensure_string_closed(state)
        return "".join(result)

    def _start_string(self, state: _ScanState, result: list[str]) -> bool:
        if state.current() != '"':
            return False
        state.in_string = True
        result.append(state.current())
        state.advance()
        return True

    def _consume_string_char(self, state: _ScanState, result: list[str]) -> None:
        char = state.current()
        result.append(char)
        if state.escape:
            state.escape = False
        elif char == "\\":
            state.escape = True
        elif char == '"':
            state.in_string = False
        state.advance()

    def _skip_line_comment(self, state: _ScanState, result: list[str]) -> bool:
        if state.current() != "/" or state.peek() != "/":
            return False
        state.advance(2)
        while state.has_more() and state.current() not in {"\n", "\r"}:
            state.advance()
        if state.has_more():
            result.append("\n")
            state.advance()
        return True

    def _skip_block_comment(self, state: _ScanState) -> bool:
        if state.current() != "/" or state.peek() != "*":
            return False
        start_line, start_col = state.line, state.col
        state.advance(2)
        while state.has_more():
            if state.current() == "*" and state.peek() == "/":
                state.advance(2)
                return True
            state.advance()
        raise ValueError(
            f"Unterminated block comment starting at line {start_line}, column {start_col}"
        )

    def _is_trailing_comma(self, state: _ScanState) -> bool:
        index = state.index + 1
        content = state.content
        while index < len(content) and content[index].isspace():
            index += 1
        return False if index >= len(content) else content[index] in {"}", "]"}

    def _ensure_string_closed(self, state: _ScanState) -> None:
        if state.in_string:
            raise ValueError(f"Unterminated string literal at line {state.line}, column {state.col}")


@dataclass
class _ScanState:
    content: str
    index: int = 0
    line: int = 1
    col: int = 1
    in_string: bool = False
    escape: bool = False

    def has_more(self) -> bool:
        return self.index < len(self.content)

    def current(self) -> str:
        return self.content[self.index]

    def peek(self) -> str:
        if self.index + 1 >= len(self.content):
            return ""
        return self.content[self.index + 1]

    def advance(self, steps: int = 1) -> None:
        for _ in range(steps):
            if not self.has_more():
                return
            char = self.current()
            if char == "\r":
                self.line += 1
                self.col = 1
                if self.peek() == "\n":
                    self.index += 1
                self.index += 1
                continue
            if char == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.index += 1