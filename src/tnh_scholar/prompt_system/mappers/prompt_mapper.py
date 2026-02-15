"""Mapper for translating prompt files to domain models."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tnh_scholar.metadata.metadata import Frontmatter

from ..domain.models import Prompt, PromptMetadata


class PromptMapper:
    """Maps transport-layer prompt data into domain objects."""

    _IMMUTABLE_REF_PATTERN = re.compile(r"^(?P<key>.+)\.v(?P<version>\d+(?:\.\d+)*)$")

    def to_file_request(self, key: str, base_path: Path) -> Path:
        """Map prompt key to a filesystem path for transport."""
        canonical_key = self._canonical_key_from_reference(key)
        return base_path / f"{canonical_key}.md"

    def to_key_from_path(self, path: Path, base_path: Path) -> str:
        """Map a prompt file path to canonical key."""
        if path.is_absolute():
            try:
                relative = path.relative_to(base_path)
            except ValueError:
                relative = path
        else:
            relative = path
        relative = relative.with_suffix("")
        return relative.as_posix()

    def to_domain_prompt(self, file_content: str, source_key: str | None = None) -> Prompt:
        """Map raw file content (including front matter) to a Prompt."""
        metadata_raw, body = self._split_frontmatter(file_content)
        metadata_raw = self._normalize_metadata(metadata_raw, source_key=source_key)
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

    def _normalize_metadata(
        self,
        metadata_raw: dict[str, Any],
        source_key: str | None = None,
    ) -> dict[str, Any]:
        """Normalize metadata fields so partial frontmatter remains usable."""
        normalized = dict(metadata_raw)
        warnings = self._extract_warnings(normalized)

        canonical_key = self._resolve_canonical_key(normalized, source_key)
        normalized["prompt_id"] = canonical_key
        normalized["key"] = canonical_key

        normalized["required_variables"] = self._coerce_list_field(
            normalized, "required_variables", warnings, warn_on_missing=True
        )
        normalized["optional_variables"] = self._coerce_list_field(
            normalized, "optional_variables", warnings, warn_on_missing=False
        )
        normalized["default_variables"] = self._coerce_dict_field(
            normalized, "default_variables", warnings, warn_on_missing=False
        )
        normalized["inputs"] = self._normalize_inputs(normalized)
        normalized["output_contract"] = self._normalize_output_contract(normalized)
        if warnings:
            normalized["warnings"] = warnings
        return normalized

    def _extract_warnings(self, metadata_raw: dict[str, Any]) -> list[str]:
        existing = metadata_raw.get("warnings")
        return [str(item) for item in existing] if isinstance(existing, list) else []

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

    def _normalize_inputs(self, metadata_raw: dict[str, Any]) -> list[dict[str, Any]]:
        raw_inputs = metadata_raw.get("inputs")
        if isinstance(raw_inputs, list):
            return [item for item in raw_inputs if isinstance(item, dict)]

        required_variables = metadata_raw.get("required_variables", [])
        optional_variables = metadata_raw.get("optional_variables", [])
        normalized_inputs: list[dict[str, Any]] = [
            {"name": str(name), "required": True, "strictness": "strict"}
            for name in required_variables
        ]
        normalized_inputs.extend(
            {"name": str(name), "required": False, "strictness": "loose"}
            for name in optional_variables
        )
        return normalized_inputs

    def _normalize_output_contract(self, metadata_raw: dict[str, Any]) -> dict[str, Any]:
        raw_contract = metadata_raw.get("output_contract")
        if isinstance(raw_contract, dict):
            return self._normalized_contract_dict(raw_contract)

        legacy_mode = metadata_raw.get("output_mode")
        if legacy_mode in ["json", "structured"]:
            return {"mode": "json"}
        if legacy_mode == "artifacts":
            return {"mode": "artifacts", "artifacts": []}
        return {"mode": "text"}

    def _normalized_contract_dict(self, raw_contract: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(raw_contract)
        artifacts = normalized.get("artifacts")
        if not isinstance(artifacts, list):
            return normalized
        converted: list[dict[str, Any]] = []
        for artifact in artifacts:
            if isinstance(artifact, str):
                converted.append({"path": artifact, "required": False})
                continue
            if isinstance(artifact, dict):
                converted.append(dict(artifact))
        normalized["artifacts"] = converted
        return normalized

    def _resolve_canonical_key(
        self,
        metadata_raw: dict[str, Any],
        source_key: str | None,
    ) -> str:
        for key_name in ("prompt_id", "key"):
            value = metadata_raw.get(key_name)
            if isinstance(value, str) and value.strip():
                return self._canonical_key_from_reference(value.strip())
        if source_key is not None:
            return self._canonical_key_from_reference(source_key)
        raise ValueError("Prompt metadata missing key/prompt_id and source key.")

    def _canonical_key_from_reference(self, key: str) -> str:
        match = self._IMMUTABLE_REF_PATTERN.match(key)
        return match.group("key") if match else key
