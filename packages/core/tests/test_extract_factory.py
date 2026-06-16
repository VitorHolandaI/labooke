import pytest
from labooke_core.extract import EpubExtractor, PdfExtractor, TextExtractor, for_format


def test_for_format_returns_pdf_extractor():
    assert isinstance(for_format("pdf"), PdfExtractor)


def test_for_format_returns_epub_extractor():
    assert isinstance(for_format("epub"), EpubExtractor)


def test_for_format_normalizes_dot_prefix():
    assert isinstance(for_format(".md"), TextExtractor)


def test_for_format_returns_text_extractor_for_txt():
    assert isinstance(for_format("txt"), TextExtractor)


def test_for_format_rejects_unknown_format():
    with pytest.raises(
        ValueError,
        match="unsupported format='docx'; expected one of pdf, epub, txt, md",
    ):
        for_format("docx")
