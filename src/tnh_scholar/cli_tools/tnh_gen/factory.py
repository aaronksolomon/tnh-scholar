from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tnh_scholar.cli_tools.tnh_gen.config_loader import CLIConfig
from tnh_scholar.cli_tools.tnh_gen.types import SettingsKwargs
from tnh_scholar.gen_ai_service.config.settings import GenAISettings
from tnh_scholar.gen_ai_service.protocols import GenAIServiceProtocol
from tnh_scholar.gen_ai_service.service import GenAIService


@dataclass
class ServiceOverrides:
    """Typed overrides passed from CLI flags into Settings."""

    model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


def cli_config_to_settings_kwargs(cli_config: CLIConfig, overrides: ServiceOverrides) -> SettingsKwargs:
    """Translate CLI configuration into kwargs for GenAI service settings."""
    payload: SettingsKwargs = {}
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
    if overrides.temperature is not None:
        payload["default_temperature"] = overrides.temperature
    if overrides.max_tokens is not None:
        payload["default_max_output_tokens"] = overrides.max_tokens
    # explicit model override stored in RenderRequest, not settings, but keep for completeness
    if overrides.model is not None:
        payload["default_model"] = overrides.model
    return payload


class ServiceFactory(Protocol):
    """Factory protocol for constructing GenAI services."""

    def create_genai_service(self, 
                             cli_config: CLIConfig, 
                             overrides: ServiceOverrides,
                             ) -> GenAIServiceProtocol:
        """Create a GenAI service given CLI config and overrides."""
        ...


class DefaultServiceFactory:
    """Default factory bridging CLI config to GenAIService."""

    def create_genai_service(self, 
                             cli_config: CLIConfig, 
                             overrides: ServiceOverrides
                             ) -> GenAIServiceProtocol:
        """Create a fully configured GenAI service instance.

        Args:
            cli_config: Effective CLI configuration.
            overrides: Execution-time overrides for model and token behavior.

        Returns:
            GenAIServiceProtocol implementation bound to current settings.
        """
        settings_kwargs = cli_config_to_settings_kwargs(cli_config, overrides)
        settings = GenAISettings(_env_file=None, **settings_kwargs) #type: ignore # pydantic mypy plugin misses
        return GenAIService(settings=settings)
