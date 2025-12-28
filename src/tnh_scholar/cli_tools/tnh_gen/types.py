from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Mapping, MutableMapping, NotRequired, TypedDict

DefaultVariables = Mapping[str, Any]
PolicyApplied = Mapping[str, Any]
VariableMap = MutableMapping[str, Any]
ConfigKey = Literal[
    "prompt_catalog_dir",
    "default_model",
    "max_dollars",
    "max_input_chars",
    "default_temperature",
    "api_key",
    "cli_path",
]


class ConfigData(TypedDict, total=False):
    prompt_catalog_dir: str | Path | None
    default_model: str | None
    max_dollars: float | None
    max_input_chars: int | None
    default_temperature: float | None
    api_key: str | None
    cli_path: str | None


class ConfigMeta(TypedDict):
    sources: list[str]
    config_files: list[str]


class ConfigValuePayload(TypedDict):
    trace_id: str
    prompt_catalog_dir: NotRequired[str | Path | None]
    default_model: NotRequired[str | None]
    max_dollars: NotRequired[float | None]
    max_input_chars: NotRequired[int | None]
    default_temperature: NotRequired[float | None]
    api_key: NotRequired[str | None]
    cli_path: NotRequired[str | None]


class ConfigShowPayload(TypedDict):
    config: ConfigData
    sources: list[str]
    config_files: list[str]
    trace_id: str


class ConfigUpdatePayload(TypedDict):
    updated: ConfigData
    target: str


class ConfigUpdateApiPayload(TypedDict):
    status: str
    updated: ConfigData
    target: str
    trace_id: str


class ConfigKeysPayload(TypedDict):
    keys: list[str]
    trace_id: str


class ConfigKeysHumanPayload(TypedDict):
    keys: list[str]


class ErrorDiagnostics(TypedDict, total=False):
    error_type: str
    error_code: str
    suggestion: NotRequired[str]


class ErrorPayload(TypedDict):
    status: str
    error: str
    diagnostics: ErrorDiagnostics
    trace_id: str


class HumanVariables(TypedDict):
    required: list[str]
    optional: list[str]


class HumanEntry(TypedDict):
    key: str
    name: str
    description: str
    variables: HumanVariables
    default_model: str | None
    tags: list[str]


class ListHumanPayload(TypedDict):
    prompts: list[HumanEntry]
    count: int


class ListApiEntry(TypedDict):
    key: str
    name: str
    description: str
    tags: list[str]
    required_variables: list[str]
    optional_variables: list[str]
    default_variables: DefaultVariables
    default_model: str | None
    output_mode: str | None
    version: str
    warnings: list[str]


class ListApiPayload(TypedDict):
    prompts: list[ListApiEntry]
    count: int
    sources: list[str]


class RunUsagePayload(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class RunResultPayload(TypedDict):
    text: str
    model: str | None
    provider: str | None
    usage: RunUsagePayload | None
    finish_reason: str | None


class RunProvenancePayload(TypedDict):
    backend: str
    model: str
    prompt_key: str
    prompt_fingerprint: str
    prompt_version: str
    started_at: str
    completed_at: str
    schema_version: str


class RunSuccessPayload(TypedDict):
    status: str
    result: RunResultPayload
    provenance: RunProvenancePayload
    warnings: list[str] | None
    prompt_warnings: list[str]
    policy_applied: PolicyApplied
    sources: list[str]
    trace_id: str


class VersionPayload(TypedDict):
    tnh_scholar: str
    tnh_gen: str
    python: str
    platform: str
    prompt_system_version: str
    genai_service_version: str
    trace_id: str


class VersionHumanPayload(TypedDict):
    tnh_scholar: str
    tnh_gen: str
    python: str
    platform: str
    prompt_system_version: str
    genai_service_version: str


class SettingsKwargs(TypedDict, total=False):
    prompt_dir: Path
    openai_api_key: str
    default_model: str
    max_dollars: float
    max_input_chars: int
    default_temperature: float
    default_max_output_tokens: int
