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


def test_rule_1_want():
    book = new_book()
    assert (book.status, book.added_at) == ("quero_ler", YESTERDAY)


def test_rule_2_started_once():
    book = new_book()
    update(book, {"status": "lendo"}, YESTERDAY)
    update(book, {"status": "quero_ler"}, TODAY)
    update(book, {"status": "lendo"}, TODAY)
    assert book.started_at == YESTERDAY


def test_rule_3_finished():
    book = new_book()
    update(book, {"status": "lido"}, TODAY)
    assert book.finished_at == TODAY


def test_rule_3_finished_once():
    book = new_book()
    update(book, {"status": "lido"}, YESTERDAY)
    update(book, {"status": "lido"}, TODAY)
    assert book.finished_at == YESTERDAY


def test_rule_4_unfinished():
    book = new_book()
    update(book, {"status": "lido"}, TODAY)
    update(book, {"status": "lendo"}, TODAY)
    assert book.finished_at is None
    assert book.status == "lendo"


def test_rule_5_dropped():
    book = new_book()
    update(book, {"status": "lido"}, YESTERDAY)
    update(book, {"status": "abandonado"}, TODAY)
    assert (book.status, book.finished_at) == ("abandonado", None)


def test_rating_keeps_status():
    book = new_book()
    update(book, {"rating": 1, "comment": "Nao terminei"}, TODAY)
    assert (book.rating, book.comment, book.status) == (1, "Nao terminei", "quero_ler")


def test_summary_months():
    old = new_book()
    update(old, {"status": "lido"}, datetime(2025, 1, 10, tzinfo=timezone.utc))
    recent = new_book(pages=50)
    update(recent, {"status": "lido"}, datetime(2026, 8, 3, tzinfo=timezone.utc))
    no_pages = new_book(pages=None)
    update(no_pages, {"status": "lido"}, datetime(2026, 8, 9, tzinfo=timezone.utc))

    res = summary([old, recent, no_pages], TODAY)
    months = {m["month"]: m for m in res["by_month"]}
    assert list(months) == ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    assert months["2026-08"] == {"month": "2026-08", "books": 2}
    assert (res["read"], res["pages_read"]) == (3, 250)
