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
    trace_id: str,
    prompt_version: str | None,
) -> str:
    """Build a YAML frontmatter block capturing provenance for saved files."""
    fp = envelope.provenance.fingerprint
    version = prompt_version or "unknown"
    lines = [
        "---",
        "tnh_scholar_generated: true",
        f"prompt_key: {fp.prompt_key}",
        f"prompt_version: \"{version}\"",
        f"model: {envelope.provenance.model}",
        f"fingerprint: {fp.prompt_content_hash}",
        f"trace_id: {trace_id}",
        f"generated_at: \"{_iso(envelope.provenance.finished_at)}\"",
        "schema_version: \"1.0\"",
        "---",
        "",
    ]
    return "\n".join(lines)


def write_output_file(
    path: Path,
    *,
    result_text: str,
    envelope: CompletionEnvelope,
    trace_id: str,
    prompt_version: str | None,
    include_provenance: bool,
) -> None:
    """Write result text to disk, optionally prefixing provenance metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if include_provenance:
        header = provenance_block(
            envelope,
            trace_id=trace_id,
            prompt_version=prompt_version,
        )
        path.write_text(f"{header}{result_text}", encoding="utf-8")
    else:
        path.write_text(result_text, encoding="utf-8")
