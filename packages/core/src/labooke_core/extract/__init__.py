"""Format-specific page and cover extraction."""

from labooke_core.extract.base import Extractor
from labooke_core.extract.epub_extractor import EpubExtractor
from labooke_core.extract.factory import for_format
from labooke_core.extract.pdf_extractor import PdfExtractor
from labooke_core.extract.text_extractor import TextExtractor

__all__ = [
    "EpubExtractor",
    "Extractor",
    "PdfExtractor",
    "TextExtractor",
    "for_format",
]
