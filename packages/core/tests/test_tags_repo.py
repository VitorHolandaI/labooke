import sqlite3

import pytest
from labooke_core.store.db import open_db
from labooke_core.store.tags_repo import TagNotFound, TagsRepo


@pytest.fixture
def repo() -> TagsRepo:
    return TagsRepo(open_db(":memory:", seed_tags=False))


def test_insert_returns_tag_with_id(repo):
    tag = repo.insert(name="Linux", slug="linux")
    assert tag.id > 0
    assert tag.name == "Linux"
    assert tag.slug == "linux"
    assert tag.color == "#888888"


def test_insert_accepts_custom_color(repo):
    tag = repo.insert(name="Security", slug="security", color="#ef4444")
    assert tag.color == "#ef4444"


def test_get_raises_when_missing(repo):
    with pytest.raises(TagNotFound, match="no tag with id=42"):
        repo.get(42)


def test_get_by_slug_round_trip(repo):
    inserted = repo.insert(name="Linux", slug="linux")
    fetched = repo.get_by_slug("linux")
    assert fetched == inserted


def test_get_by_slug_raises_when_missing(repo):
    with pytest.raises(TagNotFound, match="no tag with slug='nope'"):
        repo.get_by_slug("nope")


def test_list_all_orders_case_insensitive_by_name(repo):
    repo.insert(name="zebra", slug="zebra")
    repo.insert(name="alpha", slug="alpha")
    repo.insert(name="Beta", slug="beta")
    names = [t.name for t in repo.list_all()]
    assert names == ["alpha", "Beta", "zebra"]


def test_list_all_empty_on_fresh_db(repo):
    assert repo.list_all() == []


def test_rename_updates_name_only(repo):
    tag = repo.insert(name="lin", slug="linux")
    updated = repo.rename(tag.id, "Linux")
    assert updated.name == "Linux"
    assert updated.slug == "linux"  # unchanged


def test_recolor_updates_color(repo):
    tag = repo.insert(name="Linux", slug="linux")
    updated = repo.recolor(tag.id, "#22c55e")
    assert updated.color == "#22c55e"


def test_delete_removes_tag(repo):
    tag = repo.insert(name="Linux", slug="linux")
    repo.delete(tag.id)
    with pytest.raises(TagNotFound):
        repo.get(tag.id)


def test_delete_is_noop_for_missing_id(repo):
    repo.delete(999)  # should not raise


def test_unique_slug_constraint(repo):
    repo.insert(name="Linux", slug="linux")
    with pytest.raises(sqlite3.IntegrityError):
        repo.insert(name="Other", slug="linux")
