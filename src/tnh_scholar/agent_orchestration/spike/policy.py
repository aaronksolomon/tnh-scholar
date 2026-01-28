"""Policy defaults for the spike."""

from __future__ import annotations

from dataclasses import dataclass

from tnh_scholar.agent_orchestration.spike.models import SpikePolicy


@dataclass(frozen=True)
class SpikePolicyDefaults:
    """Default policy values for the spike."""

    blocked_command_patterns: tuple[str, ...] = (
        r"\brm\s+-r(f)?\b",
        r"\bgit\s+reset\s+--hard\b",
        r"\bgit\s+clean\s+-fdx?\b",
        r"\bgit\s+checkout\s+--(\s|$)",
        r"\bgit\s+restore\s+--(worktree|staged)\b",
        r"\bgit\s+branch\s+-D\b",
        r"\bgit\s+rebase\b",
        r"\bgit\s+merge\b",
        r"\bgit\s+push\s+--force(-with-lease)?\b",
        r"\bgit\s+commit\b",
        r"\bgit\s+push\b",
        r"\bmv\b.*(\s|/)\.git(/|\s|$)",
        r"\bcp\b.*(\s|/)\.git(/|\s|$)",
        r"\b(curl|wget|ssh|scp|rsync)\b",
        r"\b(pip|poetry|npm|brew)\b",
    )
    interactive_prompt_patterns: tuple[str, ...] = (
        r"\bconfirm\b",
        r"\bpassword\b",
        r"\bpress\s+enter\b",
        r"\b2fa\b",
        r"\botp\b",
        r"\by\/n\b",
        r"\byes\/no\b",
    )
    command_capture_patterns: tuple[str, ...] = (
        r"command:\s*(?P<command>.+)",
        r"run\s+command:\s*(?P<command>.+)",
        r"execute:\s*(?P<command>.+)",
    )


def default_spike_policy() -> SpikePolicy:
    """Build the default spike policy."""
    defaults = SpikePolicyDefaults()
    return SpikePolicy(
        blocked_command_patterns=list(defaults.blocked_command_patterns),
        interactive_prompt_patterns=list(defaults.interactive_prompt_patterns),
        command_capture_patterns=list(defaults.command_capture_patterns),
    )
