"""Prompt contract schema resolution and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError as JsonSchemaValidationError
from pydantic import BaseModel

from tnh_scholar.configuration.context import TNHContext
from tnh_scholar.exceptions import ConfigurationError


@dataclass(frozen=True)
class PromptContractSchemaPathPolicy:
    """Path policy for prompt contract schemas."""

    directory_parts: tuple[str, ...]
    suffix: str

    @classmethod
    def default(cls) -> "PromptContractSchemaPathPolicy":
        """Return the default prompt-contract path policy."""
        return cls(
            directory_parts=("schemas", "prompt-contracts"),
            suffix=".schema.json",
        )


class ResolvedPromptContractSchema(BaseModel):
    """Resolved prompt-contract schema artifact."""

    schema_ref: str
    path: Path
    document: dict[str, Any]


class PromptContractSchemaResolver:
    """Resolve and validate prompt-contract JSON Schema artifacts."""

    def __init__(
        self,
        context: TNHContext,
        policy: PromptContractSchemaPathPolicy | None = None,
    ) -> None:
        self._context = context
        self._policy = policy or PromptContractSchemaPathPolicy.default()

    @classmethod
    def for_prompt_directory(cls, prompts_base: Path) -> "PromptContractSchemaResolver":
        """Build a resolver using runtime-context discovery for a prompt directory."""
        return cls(_context_for_prompt_directory(prompts_base))

    def resolve_validated(self, schema_ref: str) -> ResolvedPromptContractSchema:
        """Resolve a schema_ref and confirm the artifact is valid JSON Schema."""
        resolved = self.resolve(schema_ref)
        self._check_schema_document(resolved)
        return resolved

    def resolve(self, schema_ref: str) -> ResolvedPromptContractSchema:
        """Resolve a schema_ref to the highest-precedence schema file."""
        relative_path = _relative_schema_path(schema_ref, self._policy)
        roots = self.search_roots()
        for root in roots:
            candidate = root / relative_path
            if candidate.is_file():
                return ResolvedPromptContractSchema(
                    schema_ref=schema_ref,
                    path=candidate,
                    document=_load_schema_document(candidate),
                )
        searched = ", ".join(str(root / relative_path) for root in roots)
        raise ConfigurationError(
            f"Prompt contract schema '{schema_ref}' was not found. Searched: {searched}"
        )

    def validate_instance(
        self,
        resolved: ResolvedPromptContractSchema,
        payload: Any,
    ) -> None:
        """Validate a JSON payload against a resolved schema."""
        Draft202012Validator(resolved.document).validate(payload)

    def search_roots(self) -> list[Path]:
        """Return schema search roots in workspace/user/built-in precedence."""
        paths: list[Path] = []
        if self._context.workspace_root is not None:
            paths.append(self._root_for(self._context.workspace_root))
        paths.append(self._root_for(self._context.user_root))
        paths.append(self._root_for(self._context.builtin_root))
        return paths

    def _check_schema_document(self, resolved: ResolvedPromptContractSchema) -> None:
        try:
            Draft202012Validator.check_schema(resolved.document)
        except SchemaError as exc:
            raise ConfigurationError(
                f"Prompt contract schema '{resolved.schema_ref}' is invalid: {exc.message}"
            ) from exc

    def _root_for(self, root: Path) -> Path:
        return root.joinpath(*self._policy.directory_parts)


def _context_for_prompt_directory(prompts_base: Path) -> TNHContext:
    prompts_path = prompts_base.resolve()
    discovered = TNHContext.discover(start_path=prompts_path)
    if discovered.workspace_root is not None:
        return discovered
    if prompts_path.name != "prompts":
        return discovered
    if prompts_path.parent in {discovered.user_root, discovered.builtin_root}:
        return discovered
    return TNHContext.discover(
        workspace_root=prompts_path.parent,
        user_root=discovered.user_root,
        start_path=prompts_path,
    )


def _relative_schema_path(
    schema_ref: str,
    policy: PromptContractSchemaPathPolicy,
) -> Path:
    parts = schema_ref.split(".")
    if not parts or any(not part.strip() or "/" in part or "\\" in part for part in parts):
        raise ConfigurationError(f"Invalid prompt contract schema_ref: '{schema_ref}'")
    return Path(*parts[:-1], f"{parts[-1]}{policy.suffix}")


def _load_schema_document(path: Path) -> dict[str, Any]:
    try:
        raw_value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Prompt contract schema file is not valid JSON: {path}") from exc
    if not isinstance(raw_value, dict):
        raise ConfigurationError(f"Prompt contract schema must be a JSON object: {path}")
    return raw_value


def format_contract_validation_error(
    *,
    schema_ref: str,
    error: json.JSONDecodeError | JsonSchemaValidationError,
) -> str:
    """Build a user-facing contract validation failure message."""
    if isinstance(error, json.JSONDecodeError):
        return (
            f"Generated output for schema '{schema_ref}' was not valid JSON: "
            f"{error.msg} at line {error.lineno} column {error.colno}."
        )
    path = error.json_path
    return f"Generated JSON did not satisfy schema '{schema_ref}' at {path}: {error.message}"
