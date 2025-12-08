"""Mapper for translating prompt files to domain models."""

from pathlib import Path
from typing import Any

from tnh_scholar.metadata.metadata import Frontmatter

from ..domain.models import Prompt, PromptMetadata


class PromptMapper:
    """Maps transport-layer prompt data into domain objects."""

    def to_file_request(self, key: str, base_path: Path) -> Path:
        """Map prompt key to a filesystem path for transport."""
        return base_path / f"{key}.md"

    def to_domain_prompt(self, file_content: str) -> Prompt:
        """Map raw file content (including front matter) to a Prompt."""
        metadata_raw, body = self._split_frontmatter(file_content)
        metadata = PromptMetadata.model_validate(metadata_raw)
        return Prompt(
            name=metadata.name,
            version=metadata.version,
            template=body,
            metadata=metadata,
        )

    def _split_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """Split YAML front matter from markdown content using shared Frontmatter helper."""
        cleaned = content.lstrip("\ufeff")
        metadata_obj, body = Frontmatter.extract(cleaned)
        metadata_raw = metadata_obj.to_dict() if metadata_obj else {}
        if not metadata_raw:
            raise ValueError("Prompt file missing or invalid YAML front matter.")
        return metadata_raw, body.lstrip()
