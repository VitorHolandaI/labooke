import numpy as np
import pytest
from labooke_core.embed import (
    EmbeddingUnavailable,
    OllamaEmbedder,
    encode_catalog_queries,
    encode_passages,
    encode_query,
)
from labooke_core.embed import encoder as encoder_module
from labooke_core.store.vectors_repo import VEC_DIM


class FakeEmbeddingTransport:
    def __init__(self, body: object) -> None:
        self.body = body
        self.calls: list[tuple[str, dict[str, object], float]] = []

    def post_json(self, url: str, payload: dict[str, object], timeout_seconds: float) -> object:
        self.calls.append((url, payload, timeout_seconds))
        return self.body


class RecordingEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def encode(self, texts) -> np.ndarray:
        self.calls.append(list(texts))
        return np.zeros((len(texts), VEC_DIM), dtype=np.float32)


def test_ollama_embedder_posts_1024_dimensions_and_normalizes():
    transport = FakeEmbeddingTransport({"embeddings": [[2.0] * VEC_DIM]})
    embedder = OllamaEmbedder("embedding-endpoint", "bge-m3", transport=transport)

    matrix = embedder.encode(["texto"])

    assert matrix.shape == (1, VEC_DIM)
    assert np.linalg.norm(matrix[0]) == pytest.approx(1.0)
    assert transport.calls[0][1] == {
        "model": "bge-m3",
        "input": ["texto"],
        "truncate": True,
    }


def test_ollama_embedder_rejects_wrong_shape():
    transport = FakeEmbeddingTransport({"embeddings": [[1.0] * 10]})
    embedder = OllamaEmbedder("embedding-endpoint", "bge-m3", transport=transport)

    with pytest.raises(EmbeddingUnavailable, match=rf"expected \(1, {VEC_DIM}\)"):
        embedder.encode(["texto"])


def test_empty_input_does_not_call_transport():
    transport = FakeEmbeddingTransport({"embeddings": []})
    matrix = OllamaEmbedder(
        "embedding-endpoint", "bge-m3", transport=transport
    ).encode([])
    assert matrix.shape == (0, VEC_DIM)
    assert transport.calls == []


def test_bge_queries_and_passages_are_sent_without_prefixes(monkeypatch):
    recorder = RecordingEmbedder()
    monkeypatch.setattr(encoder_module, "_settings_embedder", lambda: recorder)

    encode_query(["gravidade"])
    encode_catalog_queries(["livro de ciência"])
    encode_passages(["A gravidade atrai corpos."])

    assert recorder.calls[0] == ["gravidade"]
    assert recorder.calls[1] == ["livro de ciência"]
    assert recorder.calls[2] == ["A gravidade atrai corpos."]
