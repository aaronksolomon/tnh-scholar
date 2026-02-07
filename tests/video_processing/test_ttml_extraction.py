from pathlib import Path

import pytest

from tnh_scholar.video_processing import extract_text_from_ttml


def test_extract_text_from_ttml_fixture() -> None:
    ttml_path = Path("tests/fixtures/yt_dlp/ttml/sample.ttml")
    text = extract_text_from_ttml(ttml_path)
    assert text.splitlines() == ["First line.", "Second line."]


def test_extract_text_from_ttml_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.ttml"
    with pytest.raises(ValueError):
        extract_text_from_ttml(missing)
