"""Prompt rendering service."""

from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, Undefined

from ..config.policy import PromptRenderPolicy
from ..domain.models import Message, Prompt, RenderedPrompt, RenderParams
from ..domain.protocols import PromptRendererPort


class PromptRenderer(PromptRendererPort):
    """Renders prompts using configured policy."""

    def __init__(
        self,
        policy: PromptRenderPolicy,
        settings_defaults: dict[str, Any] | None = None,
    ):
        self._policy = policy
        self._settings_defaults = settings_defaults or {}

    def render(self, prompt: Prompt, params: RenderParams) -> RenderedPrompt:
        """Render prompt with templating and precedence rules."""
        merged_vars = self._merge_variables(prompt, params)
        env = Environment(
            undefined=StrictUndefined if params.strict_undefined else Undefined,
            trim_blocks=not params.preserve_whitespace,
            lstrip_blocks=not params.preserve_whitespace,
        )

        try:
            template = env.from_string(prompt.template)
            system_content = template.render(**merged_vars)
        except TemplateSyntaxError as exc:
            raise ValueError(f"Invalid prompt template: {exc}") from exc

        messages: list[Message] = []
        # ADR-A12 expects a user message even when user_input is empty to preserve shape.
        messages.append(Message(role="user", content=params.user_input or ""))

        return RenderedPrompt(system=system_content, messages=messages)

    def _merge_variables(self, prompt: Prompt, params: RenderParams) -> dict[str, Any]:
        """Merge variables according to policy precedence."""
        sources: dict[str, dict[str, Any]] = {
            "settings_defaults": dict(self._settings_defaults),
            "frontmatter_defaults": self._extract_frontmatter_defaults(prompt),
            "caller_context": dict(params.variables),
        }

        merged: dict[str, Any] = {}
        for source_name in self._policy.precedence_order:
            merged.update(sources.get(source_name, {}))
        return merged

    def _extract_frontmatter_defaults(self, prompt: Prompt) -> dict[str, Any]:
        """Extract default variable values from prompt metadata if provided."""
        metadata_dict = prompt.metadata.model_dump(exclude_none=True)
        defaults = metadata_dict.get("default_variables", {})
        return defaults if isinstance(defaults, dict) else {}
