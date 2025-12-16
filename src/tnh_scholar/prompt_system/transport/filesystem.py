"""Filesystem transport for prompt files."""

from pathlib import Path

from ..mappers.prompt_mapper import PromptMapper
from ..transport.models import PromptFileRequest, PromptFileResponse


class FilesystemTransport:
    """Reads prompt files from the filesystem."""

    def __init__(self, mapper: PromptMapper):
        self._mapper = mapper

    def read_file(self, request: PromptFileRequest) -> PromptFileResponse:
        """Read a prompt file from disk."""
        content = request.path.read_text(encoding="utf-8")
        try:
            metadata_raw, _ = self._mapper._split_frontmatter(content)
        except Exception:
            metadata_raw = {}
        return PromptFileResponse(
            content=content,
            metadata_raw=metadata_raw,
            file_hash=self._hash_content(content),
            loaded_at=self._now_iso(),
        )

    def list_files(self, base_path: Path, pattern: str = "**/*.md") -> list[Path]:
        """List prompt files under base path."""
        return sorted(base_path.glob(pattern))

    def _hash_content(self, content: str) -> str:
        import hashlib

        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _now_iso(self) -> str:
        import datetime as dt

        return dt.datetime.now(dt.timezone.utc).isoformat()
