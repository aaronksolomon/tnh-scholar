"""Derivative identity and timestamp integrity found by the journal live test."""

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from tnh_scholar.cli_tools.tnh_gen.output.provenance import _iso, write_output_file
from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope
from tnh_scholar.metadata import Frontmatter, Metadata


@pytest.mark.parametrize("structured", [False, True])
@pytest.mark.parametrize("include_provenance", [False, True])
def test_source_identity_is_namespaced(
    tmp_path: Path, envelope: CompletionEnvelope, structured: bool, include_provenance: bool
) -> None:
    source = Metadata(
        {
            "title": "Original article",
            "author": "Original author",
            "status": "current",
            "translated_by": "prior translator",
            "generated_at": "old time",
            "prompt_key": "old prompt",
            "source_metadata": {"title": "Earlier source"},
        }
    )
    output = tmp_path / ("derived.json" if structured else "derived.md")
    body = '{"concepts": []}' if structured else "# Concept inventory\n"
    write_output_file(
        output,
        result_text=body,
        envelope=envelope,
        source_metadata=source,
        trace_id="new-trace",
        prompt_version="1.0",
        include_provenance=include_provenance,
        structured_output=structured,
    )
    if structured:
        metadata = yaml.safe_load(Path(f"{output}.provenance.yaml").read_text())
        assert output.read_text() == body
    else:
        parsed, actual_body = Frontmatter.extract_from_file(output)
        metadata = parsed.to_dict()
        assert str(actual_body).strip() == body.strip()
    assert metadata["source_metadata"] == source.to_dict()
    assert all(key not in metadata for key in ("title", "author", "status", "translated_by"))
    if include_provenance:
        assert metadata["schema_version"] == "2.0"
        assert metadata["trace_id"] == "new-trace"
        assert metadata["generated_at"].endswith("Z")
    else:
        assert set(metadata) == {"source_metadata"}


@pytest.mark.parametrize(
    "stamp,expected",
    [
        (datetime(2026, 9, 17, 16, 51, 22, tzinfo=timezone(timedelta(hours=-7))), "2026-09-17T23:51:22Z"),
        (datetime(2026, 9, 17, 23, 51, 22, tzinfo=UTC), "2026-09-17T23:51:22Z"),
        (datetime(2026, 9, 17, 16, 51, 22), "2026-09-17T16:51:22"),
    ],
)
def test_timestamp_never_mislabels_local_time(stamp: datetime, expected: str) -> None:
    assert _iso(stamp) == expected
