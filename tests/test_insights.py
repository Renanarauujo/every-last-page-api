"""Testes do perfil de leitura."""

from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.insights import insights


def day(d):
    return datetime(2026, 9, d, tzinfo=timezone.utc)


def book(title, author, status, rating=None, pages=None, start=None, end=None):
    return SimpleNamespace(title=title, author=author, status=status, rating=rating, pages=pages,
                           started_at=day(start) if start else None, finished_at=day(end) if end else None,
                           added_at=day(1))


BOOKS = [
    book("A", "Tolkien, Christopher Tolkien", "read", 5, 400, 1, 11),
    book("B", "Tolkien", "read", 4, 300, 2, 12),
    book("C", "Chesterton", "read", 5, 200, 3, 5),
    book("D", "Rosa", "dropped", None, 600, 4, 6),
    book("E", "Autor Ruim", "read", 2, 100, 5, 6),
    book("F", "Tolkien", "want", 5, 900),
]


def test_liked_authors():
    res = insights(BOOKS)
    assert res["books"] == 5
    assert res["liked_authors"][0] == {"author": "Tolkien", "books": 2, "avg_rating": 4.5}
    assert [a["author"] for a in res["liked_authors"]] == ["Tolkien", "Chesterton"]


def test_disliked_authors():
    res = insights(BOOKS)
    assert {a["author"] for a in res["disliked_authors"]} == {"Rosa", "Autor Ruim"}


def test_sizes_and_pace():
    res = insights(BOOKS)
    assert res["liked_pages"] == 300
    assert res["dropped_pages"] == 600
    assert res["completion_rate"] == 80
    assert res["avg_days"] == 6
    assert res["pages_per_day"] == round(1000 / 23, 1)
    assert res["favorite"] == {"title": "A", "author": "Tolkien", "rating": 5}


def test_empty():
    res = insights([book("X", None, "want")])
    assert res["books"] == 0 and res["liked_authors"] == [] and res["favorite"] is None
    assert res["completion_rate"] is None and res["pages_per_day"] is None


def test_route(client):
    client.post("/shelf", json={"ol_key": "/works/OL1W", "title": "Livro", "author": "Autor", "pages": 100})
    client.put("/shelf/1", json={"status": "read", "rating": 5})
    res = client.get("/shelf/insights")
    assert res.status_code == 200
    assert res.json()["liked_authors"] == [{"author": "Autor", "books": 1, "avg_rating": 5.0}]
    assert res.json()["favorite"]["title"] == "Livro"
