from io import BytesIO
from pathlib import Path

from ebooklib import epub
from labooke_core.extract import EpubExtractor
from PIL import Image


def _cover_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (48, 64), color="#336699").save(buffer, format="PNG")
    return buffer.getvalue()


def make_epub(path: Path) -> Path:
    book = epub.EpubBook()
    book.set_identifier("sample-id")
    book.set_title("Sample EPUB")
    book.set_language("en")
    book.add_author("Tester")

    first = epub.EpubHtml(title="One", file_name="one.xhtml", lang="en")
    first.content = "<html><body><h1>One</h1><p>First EPUB page</p></body></html>"
    second = epub.EpubHtml(title="Two", file_name="two.xhtml", lang="en")
    second.content = "<html><body><h1>Two</h1><p>Second EPUB page</p></body></html>"

    book.add_item(first)
    book.add_item(second)
    book.toc = (first, second)
    book.spine = [first, second]
    book.add_item(epub.EpubNcx())
    book.set_cover("cover.png", _cover_bytes(), create_page=False)
    epub.write_epub(path, book)
    return path


def test_epub_pages_and_count(tmp_path):
    path = make_epub(tmp_path / "sample.epub")
    extractor = EpubExtractor()
    pages = list(extractor.pages(path))
    assert extractor.page_count(path) == 2
    assert [page.page_no for page in pages] == [1, 2]
    assert "First EPUB page" in pages[0].text
    assert "Second EPUB page" in pages[1].text


def test_epub_page_text_validates_range(tmp_path):
    path = make_epub(tmp_path / "sample.epub")
    extractor = EpubExtractor()
    assert "Second EPUB page" in extractor.page_text(path, 2)
    try:
        extractor.page_text(path, 3)
        raised = False
    except ValueError as exc:
        raised = True
        assert "page_no=3 out of range" in str(exc)
    assert raised


def test_epub_cover_thumbnail_smoke(tmp_path):
    path = make_epub(tmp_path / "sample.epub")
    destination = tmp_path / "sample.webp"
    output = EpubExtractor().write_cover_thumbnail(path, destination)
    image = Image.open(output)
    assert output == destination
    assert image.format == "WEBP"
    assert image.size[0] <= 320
    assert image.size[1] <= 480
