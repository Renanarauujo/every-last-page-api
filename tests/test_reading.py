"""Testes das regras de status."""

from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.reading import init, summary, update

YESTERDAY = datetime(2026, 9, 25, tzinfo=timezone.utc)
TODAY = datetime(2026, 9, 26, tzinfo=timezone.utc)


def new_book(pages=200):
    book = SimpleNamespace(
        pages=pages, rating=None, comment=None, started_at=None, finished_at=None
    )
    init(book, YESTERDAY)
    return book


LATER = datetime(2026, 9, 27, tzinfo=timezone.utc)


def dates(book):
    return (book.started_at, book.finished_at)


def test_rule_1_want():
    book = new_book()
    assert (book.status, book.added_at) == ("want", YESTERDAY)
    assert dates(book) == (None, None)


def test_rule_2_back_to_want():
    book = new_book()
    update(book, {"status": "reading"}, YESTERDAY)
    update(book, {"status": "want"}, TODAY)
    assert dates(book) == (None, None)


def test_rule_3_reading():
    book = new_book()
    update(book, {"status": "reading"}, TODAY)
    assert dates(book) == (TODAY, None)


def test_rule_3_reading_again():
    book = new_book()
    update(book, {"status": "reading"}, YESTERDAY)
    update(book, {"status": "read"}, TODAY)
    update(book, {"status": "reading"}, LATER)
    assert dates(book) == (LATER, None)


def test_rule_4_read():
    book = new_book()
    update(book, {"status": "reading"}, YESTERDAY)
    update(book, {"status": "read"}, TODAY)
    assert dates(book) == (YESTERDAY, TODAY)


def test_rule_4_read_directly():
    book = new_book()
    update(book, {"status": "read"}, TODAY)
    assert dates(book) == (TODAY, TODAY)


def test_same_status_keeps_dates():
    book = new_book()
    update(book, {"status": "reading"}, YESTERDAY)
    update(book, {"status": "reading"}, TODAY)
    update(book, {"status": "read"}, TODAY)
    update(book, {"status": "read"}, LATER)
    assert dates(book) == (YESTERDAY, TODAY)


def test_rule_5_dropped():
    book = new_book()
    update(book, {"status": "reading"}, YESTERDAY)
    update(book, {"status": "read"}, TODAY)
    update(book, {"status": "dropped"}, LATER)
    assert book.status == "dropped"
    assert dates(book) == (YESTERDAY, LATER)


def test_rule_5_dropped_without_start():
    book = new_book()
    update(book, {"status": "dropped"}, TODAY)
    assert dates(book) == (None, TODAY)


def test_rating_keeps_status():
    book = new_book()
    update(book, {"rating": 1, "comment": "Nao terminei"}, TODAY)
    assert (book.rating, book.comment, book.status) == (1, "Nao terminei", "want")


def test_summary_months():
    old = new_book()
    update(old, {"status": "read"}, datetime(2025, 1, 10, tzinfo=timezone.utc))
    recent = new_book(pages=50)
    update(recent, {"status": "read"}, datetime(2026, 8, 3, tzinfo=timezone.utc))
    no_pages = new_book(pages=None)
    update(no_pages, {"status": "read"}, datetime(2026, 8, 9, tzinfo=timezone.utc))

    res = summary([old, recent, no_pages], TODAY)
    months = {m["month"]: m for m in res["by_month"]}
    assert list(months) == ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    assert months["2026-08"] == {"month": "2026-08", "books": 2}
    assert (res["read"], res["pages_read"]) == (3, 250)
