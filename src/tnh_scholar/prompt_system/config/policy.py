"""Behavior policies controlling prompt rendering and validation."""

from typing import Literal

from pydantic import BaseModel


class PromptRenderPolicy(BaseModel):
    """Policy for prompt rendering precedence and behavior."""

    policy_version: str = "1.0"
    precedence_order: list[str] = [
        "caller_context",
        "frontmatter_defaults",
        "settings_defaults",
    ]
    allow_undefined_vars: bool = False
    merge_strategy: Literal["override", "merge_deep"] = "override"


class ValidationPolicy(BaseModel):
    """Policy controlling validation strictness."""

    policy_version: str = "1.0"
    mode: Literal["strict", "warn", "permissive"] = "strict"
    fail_on_missing_required: bool = True
    allow_extra_variables: bool = False

