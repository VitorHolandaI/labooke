from labooke_core import __version__
from labooke_core.config import Settings
from labooke_core.domain import Book, BookStatus, Tag


def test_version_exposed():
    assert __version__


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("LABOOKE_DATA_DIR", raising=False)
    monkeypatch.delenv("LABOOKE_IMPORT_DIR", raising=False)
    monkeypatch.delenv("LABOOKE_EMBED_MODEL", raising=False)
    settings = Settings()
    assert settings.chunk_pages == 1
    assert settings.embed_model == "intfloat/multilingual-e5-small"
    assert settings.import_dir == settings.data_dir / "inbox"


def test_book_model_constructs(tmp_path):
    tag = Tag(id=1, name="Linux", slug="linux", color="#ff00ff")
    book = Book(
        id=1,
        sha256="abc",
        path=tmp_path / "x.pdf",
        title="t",
        format="pdf",
        status=BookStatus.PENDING,
        tags=[tag],
    )
    assert book.tags[0].slug == "linux"
    assert book.status is BookStatus.PENDING
