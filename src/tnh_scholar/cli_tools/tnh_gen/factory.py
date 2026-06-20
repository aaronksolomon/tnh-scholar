from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tnh_scholar.cli_tools.tnh_gen.config_loader import CLIConfig
from tnh_scholar.cli_tools.tnh_gen.types import SettingsKwargs
from tnh_scholar.gen_ai_service.config.output_tokens import OutputTokenLimitMode
from tnh_scholar.gen_ai_service.config.settings import GenAISettings
from tnh_scholar.gen_ai_service.protocols import GenAIServiceProtocol
from tnh_scholar.gen_ai_service.service import GenAIService


@dataclass
class ServiceOverrides:
    """Typed overrides passed from CLI flags into Settings."""

    model: str | None = None
    max_tokens: int | None = None
    output_token_limit_mode: OutputTokenLimitMode | None = None
    temperature: float | None = None
    reasoning_effort: str | None = None


def cli_config_to_settings_kwargs(cli_config: CLIConfig, overrides: ServiceOverrides) -> SettingsKwargs:
    """Translate CLI configuration into kwargs for GenAI service settings."""
    payload: SettingsKwargs = {}
    _apply_cli_config(payload, cli_config)
    _apply_service_overrides(payload, overrides)
    return payload


def _apply_cli_config(payload: SettingsKwargs, cli_config: CLIConfig) -> None:
    """Copy persistent CLI config fields into GenAI settings kwargs."""
    if cli_config.prompt_catalog_dir:
        payload["prompt_dir"] = cli_config.prompt_catalog_dir
    if cli_config.api_key:
        payload["openai_api_key"] = cli_config.api_key
    if cli_config.default_model:
        payload["default_model"] = cli_config.default_model
    if cli_config.max_dollars is not None:
        payload["max_dollars"] = cli_config.max_dollars
    if cli_config.max_input_chars is not None:
        payload["max_input_chars"] = cli_config.max_input_chars


def _apply_service_overrides(payload: SettingsKwargs, overrides: ServiceOverrides) -> None:
    """Copy per-run overrides into GenAI settings kwargs."""
    if overrides.temperature is not None:
        payload["default_temperature"] = overrides.temperature
    if overrides.max_tokens is not None:
        payload["default_max_output_tokens"] = overrides.max_tokens
    if overrides.output_token_limit_mode is not None:
        payload["default_output_token_limit_mode"] = overrides.output_token_limit_mode
    payload["default_reasoning_effort"] = overrides.reasoning_effort
    # explicit model override stored in RenderRequest, not settings, but keep for completeness
    if overrides.model is not None:
        payload["default_model"] = overrides.model


class ServiceFactory(Protocol):
    """Factory protocol for constructing GenAI services."""

    def create_genai_service(
        self,
        cli_config: CLIConfig,
        overrides: ServiceOverrides,
    ) -> GenAIServiceProtocol:
        """Create a GenAI service given CLI config and overrides."""
        ...


class DefaultServiceFactory:
    """Default factory bridging CLI config to GenAIService."""

    def create_genai_service(
        self, cli_config: CLIConfig, overrides: ServiceOverrides
    ) -> GenAIServiceProtocol:
        """Create a fully configured GenAI service instance.

        Args:
            cli_config: Effective CLI configuration.
            overrides: Execution-time overrides for model and token behavior.

        Returns:
            GenAIServiceProtocol implementation bound to current settings.
        """
        settings_kwargs = cli_config_to_settings_kwargs(cli_config, overrides)
        settings = GenAISettings(_env_file=None, **settings_kwargs)  # type: ignore # pydantic mypy plugin misses
        return GenAIService(settings=settings)
