"""Embedding and chunking helpers for labooke."""

from labooke_core.embed.chunker import TextChunk, chunk_pages
from labooke_core.embed.encoder import (
    EmbeddingUnavailable,
    OllamaEmbedder,
    encode,
    encode_catalog_queries,
    encode_passages,
    encode_query,
)

__all__ = [
    "EmbeddingUnavailable",
    "OllamaEmbedder",
    "TextChunk",
    "chunk_pages",
    "encode",
    "encode_catalog_queries",
    "encode_passages",
    "encode_query",
]
