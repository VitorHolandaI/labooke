from pathlib import Path

from labooke_core.extract import TextExtractor
from PIL import Image


def make_text_file(path: Path, lines: int) -> Path:
    content = "\n".join(f"line {index}" for index in range(1, lines + 1))
    path.write_text(content, encoding="utf-8")
    return path


def test_text_pages_and_count(tmp_path):
    path = make_text_file(tmp_path / "sample.txt", lines=45)
    extractor = TextExtractor()
    pages = list(extractor.pages(path))
    assert extractor.page_count(path) == 2
    assert [page.page_no for page in pages] == [1, 2]
    assert "line 1" in pages[0].text
    assert "line 45" in pages[1].text


def test_text_page_text_validates_range(tmp_path):
    path = make_text_file(tmp_path / "sample.md", lines=2)
    extractor = TextExtractor()
    assert extractor.page_text(path, 1).startswith("line 1")
    try:
        extractor.page_text(path, 2)
        raised = False
    except ValueError as exc:
        raised = True
        assert "page_no=2 out of range" in str(exc)
    assert raised


def test_text_cover_thumbnail_smoke(tmp_path):
    path = make_text_file(tmp_path / "sample.txt", lines=1)
    destination = tmp_path / "sample.webp"
    output = TextExtractor().write_cover_thumbnail(path, destination)
    image = Image.open(output)
    assert output == destination
    assert image.format == "WEBP"
    assert image.size == (320, 480)
