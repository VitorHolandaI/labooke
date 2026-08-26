"""Bible CLI — search and browse the labooke library from the terminal."""

from __future__ import annotations

import typer

from labooke_bible._api_client import ApiClient, ApiError
from labooke_bible._history import HistoryStore

app = typer.Typer(help="Search and browse your book library.")

_client_singleton: ApiClient | None = None
_history_singleton: HistoryStore | None = None


def _client() -> ApiClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = ApiClient()
    return _client_singleton


def _history() -> HistoryStore:
    global _history_singleton
    if _history_singleton is None:
        import os
        from pathlib import Path

        data_dir = Path(os.getenv("LABOOKE_DATA_DIR", "./data"))
        _history_singleton = HistoryStore(data_dir / "bible_history.txt")
    return _history_singleton


def _abort(err: ApiError) -> None:
    typer.echo(str(err), err=True)
    raise typer.Exit(code=1)


# ── commands ──────────────────────────────────────────────────────────────────


@app.command()
def tags() -> None:
    """List all tags with book counts."""
    try:
        counts = _client().get_tags()
    except ApiError as e:
        _abort(e)
    if not counts:
        typer.echo("No tags.")
        return
    for entry in counts:
        typer.echo(f"{entry['tag']['name']} ({entry['count']})")


@app.command()
def books(
    tag: list[str] = typer.Option(default=[], help="Filter by tag slug (repeatable)."),  # noqa: B008
) -> None:
    """List books in the library, optionally filtered by tag slug."""
    try:
        client = _client()
        tag_ids = _slugs_to_ids(client, tag)
        book_list = client.get_books(tag_ids=tag_ids or None)
    except ApiError as e:
        _abort(e)
    if not book_list:
        typer.echo("No books.")
        return
    for book in book_list:
        tag_names = ", ".join(t["name"] for t in book.get("tags", [])) or "—"
        typer.echo(f"[{book['id']}] {book['title']}  [{book['format']}]  {tag_names}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query."),
    tag: list[str] = typer.Option(default=[], help="Filter by tag slug (repeatable)."),  # noqa: B008
    any_tag: bool = typer.Option(False, "--any", help="Match any tag instead of all."),
    k: int = typer.Option(10, "-k", help="Max number of results."),
    lexical: bool = typer.Option(
        False, "--lexical", help="Use title search instead of hybrid passage search."
    ),
) -> None:
    """Search the library by query. Defaults to hybrid passage search."""
    _history().push(query)
    try:
        client = _client()
        tag_ids = _slugs_to_ids(client, tag)
        hits = client.search(
            query,
            mode="lexical" if lexical else "hybrid",
            tag_ids=tag_ids or None,
            tag_mode="any" if any_tag else "all",
            k=k,
        )
        _echo_hits(hits)
    except ApiError as e:
        _abort(e)


@app.command()
def scan() -> None:
    """Ingest supported files from the import folder (LABOOKE_IMPORT_DIR)."""
    try:
        result = _client().scan()
    except ApiError as e:
        _abort(e)
    typer.echo(
        f"Scanned: {result['ingested']} ingested, "
        f"{result['skipped']} skipped, {result['failed']} failed."
    )


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def tag(
    ctx: typer.Context,
    book_id: int = typer.Argument(..., help="Book ID to edit."),
) -> None:
    """Edit tags on a book. Prefix slugs with + to add or - to remove.

    Example: bible tag 42 +linux -fiction
    """
    try:
        client = _client()
        client.get_book(book_id)  # verify exists
        slug_map = {e["tag"]["slug"]: e["tag"]["id"] for e in client.get_tags()}
        for edit in ctx.args:
            if edit.startswith("+") and edit[1:] in slug_map:
                client.attach_tag(book_id, slug_map[edit[1:]])
            elif edit.startswith("-") and edit[1:] in slug_map:
                client.detach_tag(book_id, slug_map[edit[1:]])
    except ApiError as e:
        _abort(e)


@app.command()
def read(
    book_id: int = typer.Argument(..., help="Book ID to open."),
    page: int = typer.Option(1, "-p", "--page", help="Page number to start at."),
) -> None:
    """Open the TUI pager for a book."""
    from labooke_bible._tui import run_pager

    try:
        client = _client()
        book = client.get_book(book_id)
    except ApiError as e:
        _abort(e)

    run_pager(
        get_page_text=client.get_page,
        book_id=book_id,
        title=book["title"],
        total_pages=book.get("page_count") or 1,
        start_page=page,
    )


@app.command()
def history(n: int = typer.Option(20, "-n", help="Number of entries to show.")) -> None:
    """Show recent search queries."""
    entries = _history().entries()
    if not entries:
        typer.echo("No history.")
        return
    for i, q in enumerate(entries[-n:], 1):
        typer.echo(f"{i:3}. {q}")


@app.command()
def last(
    tag: list[str] = typer.Option(default=[], help="Filter by tag slug (repeatable)."),  # noqa: B008
    any_tag: bool = typer.Option(False, "--any", help="Match any tag instead of all."),
    k: int = typer.Option(10, "-k", help="Max number of results."),
    lexical: bool = typer.Option(
        False, "--lexical", help="Use title search instead of hybrid passage search."
    ),
) -> None:
    """Re-run the most recent search query."""
    query = _history().last()
    if not query:
        typer.echo("No history.")
        return
    typer.echo(f"Searching: {query}")
    try:
        client = _client()
        tag_ids = _slugs_to_ids(client, tag)
        hits = client.search(
            query,
            mode="lexical" if lexical else "hybrid",
            tag_ids=tag_ids or None,
            tag_mode="any" if any_tag else "all",
            k=k,
        )
        _echo_hits(hits)
    except ApiError as e:
        _abort(e)


# ── helpers ───────────────────────────────────────────────────────────────────


def _echo_hits(hits: list[dict]) -> None:
    """Print flat search hits as a numbered list."""
    if not hits:
        typer.echo("No results.")
        return
    for i, hit in enumerate(hits, 1):
        typer.echo(f"{i}. [{hit['book_id']}] p{hit['page_start']}  {hit['snippet']}")


def _slugs_to_ids(client: ApiClient, slugs: list[str]) -> list[int]:
    """Return tag IDs for the given slugs, silently ignoring unknowns."""
    all_tags = {e["tag"]["slug"]: e["tag"]["id"] for e in client.get_tags()}
    return [all_tags[s] for s in slugs if s in all_tags]
