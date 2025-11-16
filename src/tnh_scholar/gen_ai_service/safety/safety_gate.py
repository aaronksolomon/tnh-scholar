"""Safety Gate.

Evaluates pre- and post-generation safety policies before finalizing output.
Integrates with rulesets defined under runtime_assets/policies/safety.

Connected modules:
  - safety.rules
  - service.GenAIService
  - models.errors.SafetyError
"""

from tnh_scholar.gen_ai_service.models.domain import CompletionResult, RenderedPrompt
from tnh_scholar.gen_ai_service.models.errors import SafetyBlocked


def pre_check(prompt: RenderedPrompt) -> None:
    """
    V1: trivial length guard using typed Message objects.

    TODO: move the hard-coded limit to a typed policy/settings source
    (e.g., ADR-A08 params policy) and inject here; no literals.
    """
    system_text = prompt.system or ""
    # `prompt.messages` is List[Message]; use attribute access
    # Normalize all message contents to strings; if content is a list, flatten by joining its parts.
    user_text_parts: list[str] = []
    for m in prompt.messages:
        c = m.content
        if isinstance(c, list):
            # join inner elements defensively, converting each element to str
            user_text_parts.append("".join(str(p) for p in c))
        else:
            user_text_parts.append(str(c))
    user_text = "".join(user_text_parts)
    content = system_text + user_text

    if len(content) > 20_000:  # temporary literal until policy wiring lands
        raise SafetyBlocked("Prompt too large")


def post_check(result: CompletionResult) -> None:
    # V1: no-op
    return