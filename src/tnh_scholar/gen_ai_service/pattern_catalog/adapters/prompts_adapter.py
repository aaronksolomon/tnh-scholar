"""Prompts Adapter (V1 per ADR-A12).

Bridges the existing `Prompt`/`PromptManager` system to the new
PromptCatalog rendering contract. This adapter:

- Loads prompts via `PromptManager`
- Renders via Prompt.apply_template (respects default fields + frontmatter + field values precedence)
- Produces a `RenderedPrompt` **and** a `Fingerprint` value object
- Computes deterministic hashes via `infra/tracking/fingerprint.py`
- Does **not** construct Provenance; that is the responsibility of GenAIService
- V1 semantics (ADR-A12): render existing prompt template into `system` 
  (via Prompt.apply_template(field_values=variables)); 
  pass caller's verbatim `RenderRequest.user_prompt` as the sole user message (no user templating).

Notes
-----
- This module performs no file I/O beyond optional access to prompt
  source bytes if prompt exposes them.
- Keep this adapter thin; all hashing rules live in `fingerprint.py`.
- Provenance is built in `provenance.py` and assembled by `GenAIService`.

V1 message shape invariants:
- system: rendered existing prompt template with `variables` 
  (via Prompt.apply_template(field_values=variables))
- messages: exactly one user message containing the verbatim `RenderRequest.user_prompt`
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

# Prompt system (import directly to avoid loading unrelated heavy deps)
from tnh_scholar.ai_text_processing.prompts import Prompt, PromptCatalog

# Fingerprinting
from tnh_scholar.gen_ai_service.infra.tracking.fingerprint import (
    hash_prompt_bytes,
    hash_user_string,
    hash_vars,
)

# Domain models (transport/domain layer)
from tnh_scholar.gen_ai_service.models.domain import (
    Fingerprint,
    Message,
    RenderedPrompt,
    RenderRequest,
    Role,
)

__all__ = [
    "PromptsAdapter",
]


@dataclass(frozen=True)
class _PromptData:
    """Uniform materialized view of a prompt.

    For V1 we depend on the canonical `Prompt` API from `prompts.py`
    (e.g. `extract_frontmatter`, `get_content_without_frontmatter`) and
    on `PromptManager.get_prompt_path` for locating the backing file
    on disk. 
    """

    key: str
    base_path: Path
    prompt: Prompt
    prompt_path: Path | None
    system_t: str | None
    user_t: str | None
    model_hint: str | None

class PromptsAdapter:
    """Render prompts and produce a Fingerprint per ADR-A12.

    API
    ---
    `render(key, request) -> tuple[RenderedPrompt, Fingerprint]`
      - Renders using Jinja2 (StrictUndefined) with `request.variables`
      - Returns a `RenderedPrompt` for the provider adapter
      - Also returns a `Fingerprint` value object that identifies what was rendered

    Notes
    -----
    - Provenance is not constructed here; it is built later in GenAIService
      from the Fingerprint plus runtime execution details.
    """

    def __init__(self, *, prompts_base: Path):
      self._base = Path(prompts_base)
      self._pm = PromptCatalog(base_path=self._base)

    # ---- Public API ----

    def render(self, request: RenderRequest) -> Tuple[RenderedPrompt, Fingerprint]:
      key = request.instruction_key
      prompt_data = self._materialize(key)

      # Variables come from request (may be empty dict)
      vars_dict: Dict[str, Any] = dict(request.variables or {})

      # Render prompt template into system via Prompt.apply_template.
      # User is verbatim caller input (V1).
      system = prompt_data.prompt.apply_template(field_values=vars_dict)
      user_raw = request.user_input

      # Build messages (minimal V1 user+optional system)
      messages = [Message(role=Role.user, content=user_raw)]
      rendered = RenderedPrompt(system=system, messages=messages)

      # Build fingerprint from prompt + variables + user input
      prompt_bytes = prompt_data.prompt.source_bytes()
      fingerprint = Fingerprint(
          prompt_key=prompt_data.key,
          prompt_name=prompt_data.prompt.name,
          prompt_base_path=str(prompt_data.base_path),
          prompt_content_hash=hash_prompt_bytes(prompt_bytes),
          variables_hash=hash_vars(vars_dict),
          user_string_hash=hash_user_string(user_raw),
      )

      return rendered, fingerprint

    # ---- Internals ----

    def _materialize(self, key: str) -> _PromptData:
        """Load a Prompt and expose the fields needed by the adapter.

        V1 deliberately relies on the stable API provided by `prompts.py`:
        - `PromptManager.load(name)` to construct the Prompt
        - `PromptManager.get_prompt_path(name)` to locate the backing file
        - `Prompt.extract_frontmatter()` to read YAML metadata
        - `Prompt.get_content_without_frontmatter()` to obtain the body
        """
        prompt: Prompt = self._pm.load(key)

        # Base path is the adapter's configured root; PromptManager is already
        # scoped to this repository.
        base_path = self._base

        # Use file on disk, if possible.
        prompt_path: Path | None = prompt.path

        # V1: existing prompts are single-body markdown templates. We treat
        # the body (without frontmatter) as the system template and do not
        # support a separate user template.
        sys_t = prompt.get_content_without_frontmatter()
        usr_t = None

        fm = prompt.extract_frontmatter()
        model_hint = fm.get("model_hint") if isinstance(fm, dict) else None
        return _PromptData(
            key=key,
            base_path=base_path,
            prompt=prompt,
            prompt_path=prompt_path,
            system_t=sys_t,
            user_t=usr_t,
            model_hint=model_hint,
        )
