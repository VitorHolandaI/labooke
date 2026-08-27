"""Tests for the TUI pager state machine (no terminal required)."""

from labooke_bible._pager import PageState, handle_key


def _state(page: int = 1, total: int = 10, scroll: int = 0, search: str | None = None) -> PageState:
    return PageState(
        book_id=1,
        title="Test Book",
        page=page,
        total_pages=total,
        scroll=scroll,
        search_query=search,
        lines=["line one", "line two", "line three", "line four", "line five"],
    )


# --- page navigation ---


def test_n_advances_to_next_page():
    s = handle_key(_state(page=3), "n")
    assert s.page == 4
    assert s.scroll == 0


def test_n_does_not_advance_past_last_page():
    s = handle_key(_state(page=10, total=10), "n")
    assert s.page == 10


def test_p_goes_to_previous_page():
    s = handle_key(_state(page=5), "p")
    assert s.page == 4
    assert s.scroll == 0


def test_p_does_not_go_before_first_page():
    s = handle_key(_state(page=1), "p")
    assert s.page == 1


def test_g_jumps_to_first_page():
    s = handle_key(_state(page=7), "g")
    assert s.page == 1
    assert s.scroll == 0


def test_G_jumps_to_last_page():
    s = handle_key(_state(page=2, total=10), "G")
    assert s.page == 10
    assert s.scroll == 0


# --- line scroll ---


def test_j_scrolls_down_one_line():
    s = handle_key(_state(scroll=0), "j")
    assert s.scroll == 1


def test_j_does_not_scroll_past_last_line():
    s = handle_key(_state(scroll=2), "j", viewport_rows=3)
    assert s.scroll == 2


def test_k_scrolls_up_one_line():
    s = handle_key(_state(scroll=3), "k")
    assert s.scroll == 2


def test_k_does_not_scroll_above_zero():
    s = handle_key(_state(scroll=0), "k")
    assert s.scroll == 0


def test_space_scrolls_down_one_viewport():
    s = handle_key(_state(), " ", viewport_rows=3)
    assert s.scroll == 2


def test_b_scrolls_up_one_viewport():
    s = handle_key(_state(scroll=2), "b", viewport_rows=2)
    assert s.scroll == 0


def test_right_arrow_advances_page():
    s = handle_key(_state(page=3, scroll=2), "right", viewport_rows=3)
    assert s.page == 4
    assert s.scroll == 0


def test_left_arrow_returns_to_previous_page():
    s = handle_key(_state(page=3, scroll=2), "left", viewport_rows=2)
    assert s.page == 2
    assert s.scroll == 0


def test_angle_brackets_change_pages():
    assert handle_key(_state(page=3), ">").page == 4
    assert handle_key(_state(page=3), "<").page == 2


def test_vertical_arrows_scroll_one_line():
    assert handle_key(_state(), "down", viewport_rows=3).scroll == 1
    assert handle_key(_state(scroll=1), "up", viewport_rows=3).scroll == 0


# --- quit ---


def test_q_signals_quit():
    s = handle_key(_state(), "q")
    assert s.quit is True


def test_other_keys_leave_state_unchanged():
    initial = _state(page=3, scroll=2)
    s = handle_key(initial, "x")
    assert s.page == 3
    assert s.scroll == 2
    assert s.quit is False


# --- in-page search ---


def test_slash_enters_search_mode():
    s = handle_key(_state(), "/")
    assert s.searching is True


def test_set_search_query_stores_query():
    from labooke_bible._pager import set_search_query

    s = set_search_query(_state(), "kernel")
    assert s.search_query == "kernel"
    assert s.searching is False


def test_set_search_query_scrolls_to_matching_line():
    from labooke_bible._pager import set_search_query

    s = set_search_query(_state(), "FOUR", viewport_rows=3)
    assert s.scroll == 2
