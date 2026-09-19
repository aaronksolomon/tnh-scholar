"""Registry-defined request compatibility, independent of provider SDK types."""

from enum import Enum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator


class ReasoningControl(str, Enum):
    """Application controls distinct from literal provider effort values."""

    AUTO = "auto"
    NONE = "none"


class TemperatureMode(str, Enum):
    """Conditions under which a model accepts temperature."""

    ALWAYS = "always"
    NEVER = "never"
    WITHOUT_REASONING = "without_reasoning"


class ModelRequestProfile(BaseModel):
    """Request rules for the existing Chat Completions transport.

    Effort names are registry data so new provider values need no code update.
    An omitted user setting uses the application default; auto omits the field.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    reasoning_efforts: tuple[Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]*$")], ...] = ()
    default_reasoning_effort: str | None = None
    temperature: TemperatureMode = TemperatureMode.ALWAYS
    temperature_without_effort: bool = False

    @model_validator(mode="after")
    def validate_efforts(self) -> Self:
        """Reject ambiguous controls and defaults outside the supported set."""
        if ReasoningControl.AUTO in self.reasoning_efforts:
            raise ValueError("auto is reserved for omitting reasoning_effort")
        if len(set(self.reasoning_efforts)) != len(self.reasoning_efforts):
            raise ValueError("reasoning_efforts must be unique")
        if self.default_reasoning_effort is not None:
            if self.default_reasoning_effort not in self.reasoning_efforts:
                raise ValueError("default_reasoning_effort must be in reasoning_efforts")
        return self

    def resolve_reasoning(self, requested: str | None, *, model: str) -> str | None:
        """Validate a literal effort, preserving the distinction between auto and none."""
        effort = self.default_reasoning_effort if requested is None else requested.strip().lower()
        if effort == ReasoningControl.AUTO:
            return None
        if effort is None or effort in self.reasoning_efforts:
            return effort
        supported = ", ".join(self.reasoning_efforts) or "(no explicit reasoning levels)"
        raise ValueError(
            f"Unsupported reasoning effort {effort!r} for {model}. Supported: {supported}; "
            "use auto to omit reasoning_effort."
        )

    def resolve_temperature(self, value: float | None, *, effort: str | None) -> float | None:
        """Omit unsupported sampling controls from the provider request."""
        match self.temperature:
            case TemperatureMode.ALWAYS:
                return value
            case TemperatureMode.WITHOUT_REASONING:
                if effort == ReasoningControl.NONE or (effort is None and self.temperature_without_effort):
                    return value
                return None
            case TemperatureMode.NEVER:
                return None
