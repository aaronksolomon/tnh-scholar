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
        metadata_raw = self._normalize_metadata(metadata_raw)
        metadata = PromptMetadata.model_validate(metadata_raw)
        return Prompt(
            name=metadata.name,
            version=metadata.version,
            template=body,
            metadata=metadata,
        )

    def _split_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """Split YAML front matter from markdown content using shared Frontmatter helper."""
        cleaned = content.lstrip("\ufeff\n\r\t ")
        metadata_obj, body = Frontmatter.extract(cleaned)
        metadata_raw = metadata_obj.to_dict() if metadata_obj else {}
        if not metadata_raw:
            raise ValueError("Prompt file missing or invalid YAML front matter.")
        return metadata_raw, body.lstrip()

    def _normalize_metadata(self, metadata_raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize metadata fields so partial frontmatter remains usable."""
        normalized = dict(metadata_raw)
        warnings = self._extract_warnings(normalized)
        normalized["required_variables"] = self._coerce_list_field(
            normalized, "required_variables", warnings, warn_on_missing=True
        )
        normalized["optional_variables"] = self._coerce_list_field(
            normalized, "optional_variables", warnings, warn_on_missing=False
        )
        normalized["default_variables"] = self._coerce_dict_field(
            normalized, "default_variables", warnings, warn_on_missing=False
        )
        if warnings:
            normalized["warnings"] = warnings
        return normalized

    def _extract_warnings(self, metadata_raw: dict[str, Any]) -> list[str]:
        existing = metadata_raw.get("warnings")
        if isinstance(existing, list):
            return [str(item) for item in existing]
        return []

    def _coerce_list_field(
        self,
        metadata_raw: dict[str, Any],
        field_name: str,
        warnings: list[str],
        *,
        warn_on_missing: bool,
    ) -> list[str]:
        value = metadata_raw.get(field_name)
        if value is None:
            if warn_on_missing:
                warnings.append(
                    f"Frontmatter field '{field_name}' missing; defaulting to []."
                )
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        warnings.append(
            f"Frontmatter field '{field_name}' invalid; expected list."
        )
        return []

    def _coerce_dict_field(
        self,
        metadata_raw: dict[str, Any],
        field_name: str,
        warnings: list[str],
        *,
        warn_on_missing: bool,
    ) -> dict[str, Any]:
        value = metadata_raw.get(field_name)
        if value is None:
            if warn_on_missing:
                warnings.append(
                    f"Frontmatter field '{field_name}' missing; defaulting to {{}}."
                )
            return {}
        if isinstance(value, dict):
            return dict(value)
        warnings.append(
            f"Frontmatter field '{field_name}' invalid; expected mapping."
        )
        return {}
