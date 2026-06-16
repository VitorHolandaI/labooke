import numpy as np
from labooke_core.embed import encode, get_default_embedder, unload_default_embedder
from labooke_core.embed import encoder as encoder_module


class FakeSentenceTransformer:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], bool, bool]] = []

    def encode(
        self,
        texts: list[str],
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> np.ndarray:
        self.calls.append((texts, convert_to_numpy, normalize_embeddings))
        return np.array([[float(index + 1)] * 384 for index in range(len(texts))])


def test_get_default_embedder_caches_by_model_name():
    first = get_default_embedder("demo-model")
    second = get_default_embedder("demo-model")
    assert first is second
    unload_default_embedder("demo-model")


def test_encode_uses_lazy_model_loader(monkeypatch):
    fake = FakeSentenceTransformer()
    monkeypatch.setattr(encoder_module, "_build_model", lambda model_name: fake)
    unload_default_embedder("demo-model")
    matrix = encode(["alpha", "beta"], model_name="demo-model")
    assert matrix.shape == (2, 384)
    assert matrix.dtype == np.float32
    assert fake.calls == [(["alpha", "beta"], True, True)]
    unload_default_embedder("demo-model")


def test_encode_empty_returns_empty_matrix_without_loading(monkeypatch):
    built: list[str] = []
    monkeypatch.setattr(
        encoder_module,
        "_build_model",
        lambda model_name: built.append(model_name) or FakeSentenceTransformer(),
    )
    unload_default_embedder("demo-model")
    matrix = encode([], model_name="demo-model")
    assert matrix.shape == (0, 384)
    assert built == []


def test_unload_default_embedder_forgets_cached_instance():
    first = get_default_embedder("demo-model")
    unload_default_embedder("demo-model")
    second = get_default_embedder("demo-model")
    assert first is not second
    unload_default_embedder("demo-model")


def test_encode_unloads_model_when_cache_disabled(monkeypatch):
    monkeypatch.setenv("LABOOKE_EMBED_CACHE_MODEL", "false")
    monkeypatch.setenv("LABOOKE_EMBED_WORKER_IDLE_SECONDS", "1")
    monkeypatch.setattr(
        encoder_module,
        "_build_model",
        lambda model_name: FakeSentenceTransformer(),
    )
    unload_default_embedder("demo-model")
    matrix = encode(["alpha"], model_name="demo-model")
    assert matrix.shape == (1, 384)
    assert "demo-model" not in encoder_module._EMBEDDERS
    encoder_module._shutdown_embed_worker()
    unload_default_embedder("demo-model")
