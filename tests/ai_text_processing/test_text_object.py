import pytest

from tnh_scholar.ai_text_processing.text_object import (
    MergeStrategy,
    SectionBoundaryError,
    SectionObject,
    SectionRange,
    TextObject,
)
from tnh_scholar.exceptions import MetadataConflictError
from tnh_scholar.metadata.metadata import Metadata
from tnh_scholar.text_processing import NumberedText


def test_validate_sections_raises_on_gap():
    num_text = NumberedText("\n".join(f"line{i}" for i in range(1, 11)))
    sections = [
        SectionObject("Section 1", SectionRange(1, 5), None),
        SectionObject("Section 2", SectionRange(7, 11), None),  # Gap at line 6
    ]
    text_obj = TextObject.model_construct(
        num_text=num_text, language="en", metadata=Metadata(), sections=sections
    )

    with pytest.raises(SectionBoundaryError) as exc_info:
        text_obj.validate_sections()

    message = str(exc_info.value).lower()
    assert "gap" in message
    assert "coverage" in message


def test_validate_sections_non_throwing_returns_errors():
    num_text = NumberedText("\n".join(f"line{i}" for i in range(1, 11)))
    sections = [
        SectionObject("Section 1", SectionRange(1, 5), None),
        SectionObject("Section 2", SectionRange(7, 11), None),  # Gap at line 6
    ]
    text_obj = TextObject.model_construct(
        num_text=num_text, language="en", metadata=Metadata(), sections=sections
    )

    errors = text_obj.validate_sections(raise_on_error=False)

    assert errors, "Expected validation errors for gap in sections"
    assert errors[0].error_type == "gap"
    assert errors[0].actual_start == 7


def test_validate_sections_success_returns_none():
    num_text = NumberedText("\n".join(f"line{i}" for i in range(1, 11)))
    sections = [
        SectionObject("Section 1", SectionRange(1, 2), None),
        SectionObject("Section 2", SectionRange(2, 11), None),
    ]
    text_obj = TextObject(num_text=num_text, language="en", sections=sections, metadata=Metadata())

    result = text_obj.validate_sections()

    assert result == []


def test_merge_metadata_deep_merge_nested_dicts():
    num_text = NumberedText("line1\nline2")
    text_obj = TextObject(
        num_text,
        metadata=Metadata(
            {
                "processing": {"stage": "translation", "model": "gpt-4"},
                "tags": ["dharma"],
            }
        ),
    )

    text_obj.merge_metadata(
        Metadata({"processing": {"version": "1.0"}, "tags": ["teaching"]}),
        strategy=MergeStrategy.DEEP_MERGE,
    )

    assert text_obj.metadata["processing"] == {
        "stage": "translation",
        "model": "gpt-4",
        "version": "1.0",
    }
    assert text_obj.metadata["tags"] == ["dharma", "teaching"]


def test_merge_metadata_preserve_does_not_override():
    num_text = NumberedText("line1")
    text_obj = TextObject(num_text, metadata=Metadata({"model": "old", "tags": ["a"]}))

    text_obj.merge_metadata(
        Metadata({"model": "new", "tags": ["b"]}),
        strategy=MergeStrategy.PRESERVE,
    )

    assert text_obj.metadata["model"] == "old"
    assert text_obj.metadata["tags"] == ["a"]


def test_merge_metadata_update_overrides():
    num_text = NumberedText("line1")
    text_obj = TextObject(num_text, metadata=Metadata({"model": "old"}))

    text_obj.merge_metadata(
        Metadata({"model": "new"}),
        strategy=MergeStrategy.UPDATE,
    )

    assert text_obj.metadata["model"] == "new"


def test_merge_metadata_fail_on_conflict_raises():
    num_text = NumberedText("line1")
    text_obj = TextObject(num_text, metadata=Metadata({"model": "old"}))

    with pytest.raises(MetadataConflictError):
        text_obj.merge_metadata(
            Metadata({"model": "new"}),
            strategy=MergeStrategy.FAIL_ON_CONFLICT,
        )


def test_merge_metadata_appends_unhashable_lists():
    num_text = NumberedText("line1")
    text_obj = TextObject(
        num_text,
        metadata=Metadata({"_provenance": [{"source": "a"}]}),
    )

    text_obj.merge_metadata(
        Metadata({"_provenance": [{"source": "b"}]}),
        strategy=MergeStrategy.DEEP_MERGE,
    )

    assert text_obj.metadata["_provenance"] == [{"source": "a"}, {"source": "b"}]


def test_merge_metadata_provenance_tracking():
    text_obj = TextObject(NumberedText("line1"))
    text_obj.merge_metadata(
        Metadata({"model": "gpt-4"}),
        strategy=MergeStrategy.PRESERVE,
        source="genai_service",
    )

    assert "_provenance" in text_obj.metadata
    provenance = text_obj.metadata["_provenance"]
    assert isinstance(provenance, list)
    assert provenance[0]["source"] == "genai_service"
    assert provenance[0]["strategy"] == MergeStrategy.PRESERVE.value
