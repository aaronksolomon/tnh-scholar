from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from tnh_scholar.configuration.context import TNHContext
from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.prompt_system.service.contract_schema import (
    PromptContractSchemaResolver,
    _load_schema_document,
    _relative_schema_path,
)


def _write_schema(base: Path, schema_ref: str, payload: dict) -> Path:
    relative = Path("schemas", "prompt-contracts", *schema_ref.split(".")[:-1])
    path = base / relative / f"{schema_ref.split('.')[-1]}.schema.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_schema_resolver_uses_workspace_user_builtin_precedence(tmp_path: Path):
    workspace_root = tmp_path / "workspace"
    user_root = tmp_path / "user"
    builtin_root = tmp_path / "builtin"
    schema_ref = "tnh.testing.echo.v1"
    workspace_schema = {"type": "object", "required": ["workspace"]}
    user_schema = {"type": "object", "required": ["user"]}
    builtin_schema = {"type": "object", "required": ["builtin"]}

    workspace_path = _write_schema(workspace_root, schema_ref, workspace_schema)
    _write_schema(user_root, schema_ref, user_schema)
    _write_schema(builtin_root, schema_ref, builtin_schema)
    context = TNHContext(
        builtin_root=builtin_root,
        workspace_root=workspace_root,
        user_root=user_root,
        correlation_id="corr",
        session_id="sess",
    )

    resolved = PromptContractSchemaResolver(context).resolve_validated(schema_ref)

    assert resolved.path == workspace_path
    assert resolved.document == workspace_schema


def test_schema_resolver_rejects_missing_schema(tmp_path: Path):
    context = TNHContext(
        builtin_root=tmp_path / "builtin",
        workspace_root=tmp_path / "workspace",
        user_root=tmp_path / "user",
        correlation_id="corr",
        session_id="sess",
    )

    with pytest.raises(ConfigurationError, match="was not found"):
        PromptContractSchemaResolver(context).resolve_validated("tnh.testing.missing.v1")


def test_schema_resolver_rejects_invalid_schema_ref_syntax():
    with pytest.raises(ConfigurationError, match="Invalid prompt contract schema_ref"):
        _relative_schema_path("tnh..bad.v1")

    with pytest.raises(ConfigurationError, match="Invalid prompt contract schema_ref"):
        _relative_schema_path("../escape")


def test_schema_resolver_rejects_invalid_schema_document(tmp_path: Path):
    builtin_root = tmp_path / "builtin"
    _write_schema(builtin_root, "tnh.testing.bad.v1", {"type": 123})
    context = TNHContext(
        builtin_root=builtin_root,
        workspace_root=None,
        user_root=tmp_path / "user",
        correlation_id="corr",
        session_id="sess",
    )

    with pytest.raises(ConfigurationError, match="is invalid"):
        PromptContractSchemaResolver(context).resolve_validated("tnh.testing.bad.v1")


def test_schema_resolver_rejects_non_object_schema_document(tmp_path: Path):
    schema_path = tmp_path / "non_object.schema.json"
    schema_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    with pytest.raises(ConfigurationError, match="must be a JSON object"):
        _load_schema_document(schema_path)


def test_schema_resolver_rejects_malformed_json_schema_document(tmp_path: Path):
    schema_path = tmp_path / "malformed.schema.json"
    schema_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="is not valid JSON"):
        _load_schema_document(schema_path)


def test_schema_resolver_validates_json_instances(tmp_path: Path):
    builtin_root = tmp_path / "builtin"
    schema_ref = "tnh.testing.echo.v1"
    _write_schema(
        builtin_root,
        schema_ref,
        {
            "type": "object",
            "required": ["message"],
            "additionalProperties": False,
            "properties": {"message": {"type": "string"}},
        },
    )
    context = TNHContext(
        builtin_root=builtin_root,
        workspace_root=None,
        user_root=tmp_path / "user",
        correlation_id="corr",
        session_id="sess",
    )
    resolver = PromptContractSchemaResolver(context)
    resolved = resolver.resolve_validated(schema_ref)

    resolver.validate_instance(resolved, {"message": "ok"})

    with pytest.raises(JsonSchemaValidationError):
        resolver.validate_instance(resolved, {"message": 1})
