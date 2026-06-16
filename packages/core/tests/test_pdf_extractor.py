from pathlib import Path

import fitz
from labooke_core.extract import PdfExtractor
from PIL import Image


def make_pdf(path: Path) -> Path:
    document = fitz.open()
    first = document.new_page()
    first.insert_text((72, 72), "First PDF page")
    second = document.new_page()
    second.insert_text((72, 72), "Second PDF page")
    document.save(path)
    document.close()
    return path


def test_pdf_pages_and_count(tmp_path):
    path = make_pdf(tmp_path / "sample.pdf")
    extractor = PdfExtractor()
    pages = list(extractor.pages(path))
    assert extractor.page_count(path) == 2
    assert [page.page_no for page in pages] == [1, 2]
    assert "First PDF page" in pages[0].text
    assert "Second PDF page" in pages[1].text


def test_pdf_page_text_validates_range(tmp_path):
    path = make_pdf(tmp_path / "sample.pdf")
    extractor = PdfExtractor()
    assert "Second PDF page" in extractor.page_text(path, 2)
    try:
        extractor.page_text(path, 3)
        raised = False
    except ValueError as exc:
        raised = True
        assert "page_no=3 out of range" in str(exc)
    assert raised


def test_pdf_cover_thumbnail_smoke(tmp_path):
    path = make_pdf(tmp_path / "sample.pdf")
    destination = tmp_path / "sample.webp"
    output = PdfExtractor().write_cover_thumbnail(path, destination)
    image = Image.open(output)
    assert output == destination
    assert image.format == "WEBP"
    assert image.size[0] <= 320
    assert image.size[1] <= 480
