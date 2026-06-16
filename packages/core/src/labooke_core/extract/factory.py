"""Extractor selection by file format."""

from __future__ import annotations

from labooke_core.extract.base import Extractor
from labooke_core.extract.epub_extractor import EpubExtractor
from labooke_core.extract.pdf_extractor import PdfExtractor
from labooke_core.extract.text_extractor import TextExtractor

_EXTRACTORS: dict[str, Extractor] = {
    "pdf": PdfExtractor(),
    "epub": EpubExtractor(),
    "txt": TextExtractor(),
    "md": TextExtractor(),
}


def for_format(fmt: str) -> Extractor:
    """Return the extractor instance for ``fmt``.

    Example:
        >>> for_format(".md").__class__.__name__
        'TextExtractor'
    """
    normalized = fmt.strip().lower().lstrip(".")
    extractor = _EXTRACTORS.get(normalized)
    if extractor is None:
        raise ValueError(
            f"unsupported format={fmt!r}; expected one of pdf, epub, txt, md"
        )
    return extractor
