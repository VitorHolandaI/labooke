from pathlib import Path

from labooke_core.extract import EpubExtractor, PdfExtractor, TextExtractor
from PIL import Image

FIXTURES = Path(__file__).parent / "fixtures"


def _assert_thumbnail(output: Path) -> None:
    image = Image.open(output)
    assert image.format == "WEBP"
    assert image.size[0] <= 320
    assert image.size[1] <= 480


def test_pdf_fixture_round_trip(tmp_path):
    extractor = PdfExtractor()
    source = FIXTURES / "sample.pdf"
    pages = list(extractor.pages(source))
    assert extractor.page_count(source) == 2
    assert [page.page_no for page in pages] == [1, 2]
    assert "Sample PDF fixture page one" in pages[0].text
    assert "semantic search target" in pages[1].text
    _assert_thumbnail(extractor.write_cover_thumbnail(source, tmp_path / "pdf.webp"))


def test_epub_fixture_round_trip(tmp_path):
    extractor = EpubExtractor()
    source = FIXTURES / "sample.epub"
    pages = list(extractor.pages(source))
    assert extractor.page_count(source) == 2
    assert [page.page_no for page in pages] == [1, 2]
    assert "Sample EPUB fixture page one" in pages[0].text
    assert "Sample EPUB fixture page two" in pages[1].text
    _assert_thumbnail(extractor.write_cover_thumbnail(source, tmp_path / "epub.webp"))


def test_txt_fixture_round_trip(tmp_path):
    extractor = TextExtractor()
    source = FIXTURES / "sample.txt"
    pages = list(extractor.pages(source))
    assert extractor.page_count(source) == 1
    assert pages[0].page_no == 1
    assert "Sample TXT fixture" in pages[0].text
    assert "end of the fixture" in pages[0].text
    _assert_thumbnail(extractor.write_cover_thumbnail(source, tmp_path / "txt.webp"))


def test_md_fixture_round_trip(tmp_path):
    extractor = TextExtractor()
    source = FIXTURES / "sample.md"
    pages = list(extractor.pages(source))
    assert extractor.page_count(source) == 1
    assert "Sample Markdown Fixture" in pages[0].text
    assert "Section Two" in pages[0].text
    _assert_thumbnail(extractor.write_cover_thumbnail(source, tmp_path / "md.webp"))
