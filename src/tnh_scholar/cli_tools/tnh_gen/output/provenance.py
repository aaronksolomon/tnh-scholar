from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope, CompletionOutcomeStatus
from tnh_scholar.metadata import Frontmatter, Metadata


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
    source_metadata: Metadata | None = None,
    trace_id: str,
    prompt_version: str | None,
) -> str:
    """Build a YAML frontmatter block capturing provenance for saved files."""
    fp = envelope.provenance.fingerprint
    version = prompt_version or "unknown"
    provenance_metadata = Metadata(
        {
            "tnh_scholar_generated": True,
            "prompt_key": fp.prompt_key,
            "prompt_version": version,
            "model": envelope.provenance.model,
            "fingerprint": fp.prompt_content_hash,
            "trace_id": trace_id,
            "generated_at": _iso(envelope.provenance.finished_at),
            "schema_version": "1.0",
        }
    )
    merged_metadata = provenance_metadata
    if source_metadata:
        merged_metadata = source_metadata | provenance_metadata
    return Frontmatter.generate(merged_metadata)


def write_output_file(
    path: Path,
    *,
    result_text: str,
    envelope: CompletionEnvelope,
    source_metadata: Metadata | None = None,
    trace_id: str,
    prompt_version: str | None,
    include_provenance: bool,
) -> None:
    """Write result text to disk, optionally prefixing provenance metadata."""
    if envelope.outcome is CompletionOutcomeStatus.FAILED:
        raise ValueError("Cannot write output for a failed completion outcome")
    path.parent.mkdir(parents=True, exist_ok=True)
    if include_provenance:
        header = provenance_block(
            envelope,
            source_metadata=source_metadata,
            trace_id=trace_id,
            prompt_version=prompt_version,
        )
        path.write_text(f"{header}{result_text}", encoding="utf-8")
    elif source_metadata:
        path.write_text(f"{Frontmatter.generate(source_metadata)}{result_text}", encoding="utf-8")
    else:
        path.write_text(result_text, encoding="utf-8")
