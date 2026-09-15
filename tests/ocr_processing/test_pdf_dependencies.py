"""Exercise the OCR extra's PDF and image integration without cloud credentials."""

from pathlib import Path

import pytest


def test_pdf_image_round_trip(tmp_path: Path) -> None:
    """Read an embedded image through the project's declared PDF dependency."""
    pymupdf = pytest.importorskip("pymupdf")
    pytest.importorskip("google.cloud.vision")
    image_module = pytest.importorskip("PIL.Image")
    from tnh_scholar.ocr_processing import ocr_processing as ocr

    pdf_path = tmp_path / "scanned-page.pdf"
    image = image_module.new("RGB", (20, 30), color="red")
    with pymupdf.open() as document:
        page = document.new_page(width=72, height=144)
        page.insert_image(page.rect, stream=ocr.pil_to_bytes(image))
        document.save(pdf_path)
    with ocr.load_pdf_pages(pdf_path) as document:
        dimensions = ocr.get_page_dimensions(document[0])
        extracted = ocr.extract_image_from_page(document[0])
        assert (dimensions["width_in"], dimensions["height_in"]) == (1, 2)
        assert (dimensions["width_px"], dimensions["height_px"]) == (20, 30)
        assert extracted.size == (20, 30)
        assert extracted.getpixel((0, 0)) == (255, 0, 0)
