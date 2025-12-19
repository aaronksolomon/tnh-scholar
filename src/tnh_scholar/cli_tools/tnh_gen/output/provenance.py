from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope


def _iso(dt: datetime) -> str:
    """Format datetime without microseconds and with trailing Z.

    Args:
        dt: Datetime value to format.

    Returns:
        ISO8601 string suitable for provenance headers.
    """
    return f"{dt.replace(microsecond=0).isoformat()}Z"


def provenance_block(
    envelope: CompletionEnvelope,
    *,
    correlation_id: str,
    prompt_version: str | None,
) -> str:
    """Build an HTML comment block capturing provenance for saved files."""
    fp = envelope.provenance.fingerprint
    lines = [
        "<!--",
        "TNH-Scholar Generated Content",
        f"Prompt: {fp.prompt_key} ({prompt_version or f'v?-{fp.prompt_key}'})",
        f"Model: {envelope.provenance.model}",
        f"Fingerprint: {fp.prompt_content_hash}",
        f"Correlation ID: {correlation_id}",
        f"Generated: {_iso(envelope.provenance.finished_at)}",
        "-->",
        "",
    ]
    return "\n".join(lines)


def write_output_file(
    path: Path,
    *,
    result_text: str,
    envelope: CompletionEnvelope,
    correlation_id: str,
    prompt_version: str | None,
    include_provenance: bool,
) -> None:
    """Write result text to disk, optionally prefixing provenance metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if include_provenance:
        header = provenance_block(
            envelope,
            correlation_id=correlation_id,
            prompt_version=prompt_version,
        )
        path.write_text(f"{header}{result_text}", encoding="utf-8")
    else:
        path.write_text(result_text, encoding="utf-8")
