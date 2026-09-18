from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope, CompletionOutcomeStatus
from tnh_scholar.metadata import Frontmatter, Metadata


def _iso(dt: datetime) -> str:
    """Normalize aware timestamps to UTC; never invent a zone for legacy data."""
    if dt.utcoffset() is None:
        return dt.replace(microsecond=0).isoformat()
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_provenance(source_metadata: Metadata | None) -> Metadata:
    """Preserve input identity separately from the generated document's identity."""
    if not source_metadata:
        return Metadata()
    return Metadata({"source_metadata": source_metadata.to_dict()})


def provenance_block(
    envelope: CompletionEnvelope,
    *,
    source_metadata: Metadata | None = None,
    trace_id: str,
    prompt_version: str | None,
) -> str:
    """Build a YAML frontmatter block capturing provenance for saved files."""
    return str(
        Frontmatter.generate(
            provenance_metadata(
                envelope,
                source_metadata=source_metadata,
                trace_id=trace_id,
                prompt_version=prompt_version,
            )
        )
    )


def provenance_metadata(
    envelope: CompletionEnvelope,
    *,
    source_metadata: Metadata | None = None,
    trace_id: str,
    prompt_version: str | None,
) -> Metadata:
    """Build derivative provenance with namespaced input metadata (schema 2.0)."""
    fp = envelope.provenance.fingerprint
    version = prompt_version or "unknown"
    generated_metadata = Metadata(
        {
            "tnh_scholar_generated": True,
            "prompt_key": fp.prompt_key,
            "prompt_version": version,
            "model": envelope.provenance.model,
            "fingerprint": fp.prompt_content_hash,
            "trace_id": trace_id,
            "generated_at": _iso(envelope.provenance.finished_at),
            "schema_version": "2.0",
        }
    )
    return source_provenance(source_metadata) | generated_metadata


def sidecar_path(path: Path) -> Path:
    """Return the provenance sidecar path for a structured output artifact."""
    return path.with_name(f"{path.name}.provenance.yaml")


def write_output_file(
    path: Path,
    *,
    result_text: str,
    envelope: CompletionEnvelope,
    source_metadata: Metadata | None = None,
    trace_id: str,
    prompt_version: str | None,
    include_provenance: bool,
    structured_output: bool = False,
) -> None:
    """Write result text to disk, optionally prefixing provenance metadata."""
    if envelope.outcome is CompletionOutcomeStatus.FAILED:
        raise ValueError("Cannot write output for a failed completion outcome")
    path.parent.mkdir(parents=True, exist_ok=True)
    if structured_output:
        path.write_text(result_text, encoding="utf-8")
        if include_provenance:
            sidecar = sidecar_path(path)
            metadata = provenance_metadata(
                envelope,
                source_metadata=source_metadata,
                trace_id=trace_id,
                prompt_version=prompt_version,
            )
            sidecar.write_text(metadata.to_yaml(), encoding="utf-8")
        elif source_metadata:
            sidecar = sidecar_path(path)
            sidecar.write_text(source_provenance(source_metadata).to_yaml(), encoding="utf-8")
        return
    if include_provenance:
        header = provenance_block(
            envelope,
            source_metadata=source_metadata,
            trace_id=trace_id,
            prompt_version=prompt_version,
        )
        path.write_text(f"{header}{result_text}", encoding="utf-8")
    elif source_metadata:
        header = str(Frontmatter.generate(source_provenance(source_metadata)))
        path.write_text(f"{header}{result_text}", encoding="utf-8")
    else:
        path.write_text(result_text, encoding="utf-8")
