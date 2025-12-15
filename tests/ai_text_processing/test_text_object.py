import json
from pathlib import Path
from typing import cast

import pytest

from tnh_scholar.ai_text_processing import text_object as text_module
from tnh_scholar.ai_text_processing.text_object import (
    AIResponse,
    LoadConfig,
    LogicalSection,
    MergeStrategy,
    ProcessMetadata,
    SectionBoundaryError,
    SectionObject,
    SectionRange,
    StorageFormat,
    TextObject,
    TextObjectInfo,
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
    text_obj = TextObject(
        num_text=num_text, language="en", metadata=Metadata(), sections=sections, validate_on_init=False
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
    text_obj = TextObject(
        num_text=num_text, language="en", metadata=Metadata(), sections=sections, validate_on_init=False
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


def test_merge_metadata_fail_on_conflict_without_overlap_updates():
    obj = TextObject(NumberedText("line1"), metadata=Metadata({"x": 1}))
    obj.merge_metadata(Metadata({"y": 2}), strategy=MergeStrategy.FAIL_ON_CONFLICT)
    assert obj.metadata["y"] == 2


def test_merge_metadata_deep_merge_scalar_override_branch():
    obj = TextObject(NumberedText("line1"), metadata=Metadata({"a": {"x": 1}, "b": 1}))
    obj.merge_metadata(Metadata({"a": {"x": 2}, "b": 2}), strategy=MergeStrategy.DEEP_MERGE)
    assert obj.metadata["a"]["x"] == 2
    assert obj.metadata["b"] == 2


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


def test_transform_returns_new_instance_without_mutating_original():
    original = TextObject(
        NumberedText("line1\nline2"),
        language="en",
        sections=[SectionObject("s1", SectionRange(1, 2), None)],
        metadata=Metadata({"stage": "initial"}),
    )

    updated = original.transform(
        data_str="line1\nline2\nline3",
        language="fr",
        metadata=Metadata({"stage": "translated"}),
    )

    # Original remains unchanged
    assert original.language == "en"
    assert original.num_text.size == 2
    assert original.metadata["stage"] == "initial"

    # New instance reflects updates
    assert updated is not original
    assert updated.language == "fr"
    assert updated.num_text.size == 3
    assert updated.metadata["stage"] == "translated"
    transformed_with_process = updated.transform(
        process_metadata=ProcessMetadata(
            identifier="proc",
            description="d",
            step="step1",
            processor="p",
        )
    )
    assert transformed_with_process.metadata.get("tnh_processing")


def test_metadata_merger_unknown_strategy_raises():
    merger = text_module._MetadataMerger(Metadata({"a": 1}), Metadata({"b": 2}))
    with pytest.raises(ValueError):
        merger.merge(cast(MergeStrategy, "bogus"))


def test_load_config_validates_xor_and_reads_source(tmp_path: Path):
    with pytest.raises(ValueError):
        LoadConfig(format=StorageFormat.JSON, source_str="a", source_file=tmp_path / "x.txt")

    cfg = LoadConfig(format=StorageFormat.JSON, source_str="hello")
    assert cfg.get_source_text() == "hello"

    file = tmp_path / "src.txt"
    file.write_text("from file")
    cfg_file = LoadConfig(format=StorageFormat.JSON, source_file=file)
    assert cfg_file.get_source_text() == "from file"


def test_iterates_sections_and_get_section_content(tmp_path: Path):
    num_text = NumberedText("line1\nline2")
    sections = [SectionObject("s1", SectionRange(1, 2), None)]
    text_obj = TextObject(num_text=num_text, sections=sections, metadata=Metadata())

    entries = list(text_obj)
    assert len(entries) == 1
    assert entries[0].content == "line1\nline2"
    assert text_obj.get_section_content(0) == "line1\nline2"

    with pytest.raises(IndexError):
        text_obj.get_section_content(1)

    with pytest.raises(ValueError):
        TextObject(NumberedText("x")).get_section_content(0)


def test_str_includes_frontmatter():
    text_obj = TextObject(NumberedText("body line"), metadata=Metadata({"author": "tnh"}))
    rendered = str(text_obj)
    assert rendered.startswith("---")
    assert "author: tnh" in rendered
    assert "body line" in rendered


def test_from_str_merges_frontmatter_and_metadata():
    content = "---\nlang: en\n---\nLine1\nLine2"
    obj = TextObject.from_str(content, metadata=Metadata({"extra": "yes"}))
    assert obj.metadata["lang"] == "en"
    assert obj.metadata["extra"] == "yes"
    assert obj.content.strip().splitlines()[0] == "Line1"


def test_from_response_builds_sections_and_metadata():
    ai_resp = AIResponse(
        document_summary="summary",
        document_metadata="lang: en",
        key_concepts="concepts",
        narrative_context="ctx",
        language="en",
        sections=[
            LogicalSection(start_line=1, title="s1"),
            LogicalSection(start_line=2, title="s2"),
        ],
    )
    num_text = NumberedText("l1\nl2\nl3")
    obj = TextObject.from_response(ai_resp, Metadata({"base": True}), num_text)
    assert obj.metadata["ai_summary"] == "summary"
    assert len(obj.sections) == 2
    assert obj.sections[0].section_range.start == 1
    assert obj.sections[1].section_range.start == 2


def test_export_and_from_info_round_trip(tmp_path: Path):
    num_text = NumberedText("l1\nl2")
    sections = [SectionObject("s1", SectionRange(1, 2), None)]
    obj = TextObject(num_text=num_text, language="en", sections=sections, metadata=Metadata({"k": "v"}))
    src_file = tmp_path / "source.txt"
    src_file.write_text("l1\nl2")

    info = obj.export_info(source_file=src_file)
    assert info.source_file == src_file.resolve()

    new_obj = TextObject.from_info(info, Metadata({"extra": "y"}), num_text)
    assert new_obj.metadata["k"] == "v"
    assert new_obj.metadata["extra"] == "y"


def test_from_section_file_and_load_json(tmp_path: Path):
    # Prepare source content
    content_path = tmp_path / "content.txt"
    content_path.write_text("body1\nbody2")
    # Build TextObject and persist info JSON
    obj = TextObject(NumberedText("body1\nbody2"), language="en", sections=[], metadata=Metadata({"m": 1}))
    info = obj.export_info(source_file=content_path)
    info_path = tmp_path / "info.json"
    info_path.write_text(info.model_dump_json())

    # Load via section file
    loaded = TextObject.from_section_file(info_path)
    assert loaded.content.startswith("body1")
    assert loaded.metadata["m"] == 1

    # Load via config source_str
    info_path2 = tmp_path / "info2.json"
    info_path2.write_text(info.model_dump_json())
    loaded2 = TextObject.from_section_file(info_path2, source="override content")
    assert loaded2.content.startswith("override content")


def test_save_and_load_text_and_json(tmp_path: Path):
    obj = TextObject(NumberedText("line1\nline2"), language="en", sections=[], metadata=Metadata({"k": "v"}))

    text_path = tmp_path / "out.txt"
    obj.save(text_path, output_format=StorageFormat.TEXT)
    loaded_text = TextObject.load(text_path)
    assert "line1" in loaded_text.content

    json_path = tmp_path / "out.json"
    obj.save(json_path, output_format=StorageFormat.JSON, pretty=False)
    loaded_json = TextObject.load(
        json_path, config=LoadConfig(format=StorageFormat.JSON, source_str="line1\nline2")
    )
    assert loaded_json.metadata["k"] == "v"

    with pytest.raises(ValueError):
        obj.save(tmp_path / "bad", output_format="bogus")

    with pytest.raises(ValueError):
        TextObject.load(json_path, config=LoadConfig(format=cast(StorageFormat, "bogus")))


def test_iter_raises_when_no_sections():
    obj = TextObject(NumberedText("only line"))
    with pytest.raises(ValueError):
        list(obj)
    with pytest.raises(ValueError):
        obj.validate_sections()


def test_merge_metadata_legacy_and_update_metadata():
    obj = TextObject(NumberedText("line"), metadata=Metadata({"k": "v"}))
    obj.merge_metadata_legacy(Metadata({"k": "new"}), override=True)
    assert obj.metadata["k"] == "new"

    obj.update_metadata(extra="yes")
    assert obj.metadata["extra"] == "yes"


def test_from_section_file_missing_source(tmp_path: Path):
    info_path = tmp_path / "info.json"
    info_payload = {
        "source_file": None,
        "language": "en",
        "sections": [],
        "metadata": {},
    }
    info_path.write_text(json.dumps(info_payload))
    with pytest.raises(ValueError):
        TextObject.from_section_file(info_path)

    with pytest.raises(FileNotFoundError):
        TextObject.from_section_file(tmp_path / "nope.json")


def test_save_invalid_non_string_format(tmp_path: Path):
    obj = TextObject(NumberedText("line1"), language="en", sections=[], metadata=Metadata())
    with pytest.raises(ValueError):
        obj.save(tmp_path / "out", output_format=123)  # type: ignore[arg-type]


def test_properties_accessors():
    obj = TextObject(NumberedText("l1\nl2"), language="en", sections=[], metadata=Metadata({"a": 1}))
    assert obj.section_count == 0
    assert obj.last_line_num == 2
    assert "a: 1" in obj.metadata_str
    assert obj.numbered_content.startswith("1:")


def test_section_boundary_error_overlap_message():
    from tnh_scholar.text_processing.numbered_text import SectionValidationError

    err = SectionValidationError(
        error_type="overlap",
        section_index=1,
        section_input_index=1,
        expected_start=2,
        actual_start=1,
        message="overlap",
    )
    coverage_report = {
        "coverage_pct": 100.0,
        "covered_lines": 2,
        "total_lines": 2,
        "gaps": [],
        "overlaps": [{"lines": [1, 2]}],
    }
    ex = SectionBoundaryError([err], coverage_report)
    assert "Overlapping lines" in str(ex)


def test_textobjectinfo_metadata_coercion_and_validation():
    info = TextObjectInfo(
        source_file=None,
        language="en",
        sections=[],
        metadata={"k": "v"},
    )
    assert isinstance(info.metadata, Metadata)
    with pytest.raises(ValueError):
        TextObjectInfo(source_file=None, language="en", sections=[], metadata="bad")  # type: ignore[arg-type]
    # model_construct bypasses validators; invoke post-init manually to coerce
    raw = TextObjectInfo.model_construct(source_file=None, language="en", sections=[], metadata={"k": "v"})
    raw.model_post_init(None)
    assert isinstance(raw.metadata, Metadata)
    with pytest.raises(ValueError):
        bad = TextObjectInfo.model_construct(  # type: ignore[arg-type]
            source_file=None, language="en", sections=[], metadata=123
        )
        bad.model_post_init(None)


def test_merge_metadata_handles_non_list_provenance_and_none_input():
    obj = TextObject(NumberedText("line"), metadata=Metadata({"_provenance": "oops"}))
    obj.merge_metadata(Metadata({"new": 1}), source="src")
    assert isinstance(obj.metadata["_provenance"], list)
    obj.merge_metadata(None)
