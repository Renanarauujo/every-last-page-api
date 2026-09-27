"""Testes do tipo do livro: classificacao, edicao e perfil."""

import httpx
import pytest
from sqlalchemy import create_engine, inspect, text

from app import db as db_module
from app.main import app
from app.models.book import Genre
from app.services import open_library
from app.services.genres import classify


@pytest.mark.parametrize(
    "subjects,expected",
    [
        (["Fantasy", "hobbits", "dragons", "Fiction"], Genre.fantasy),
        (["Rhetoric", "Grammar", "Critical thinking", "Philosophy"], Genre.education),
        (["Apologetics", "Christianity", "History", "Religion & Spirituality"], Genre.religion),
        (["Fiction", "Psychological fiction", "Russian literature", "Mystery fiction"], Genre.fiction),
        (["Poetry", "Italian poetry", "Medieval Literature"], Genre.poetry),
        (["Fiction", "Historical fiction", "Catholic Church"], Genre.fiction),
        (["Fantasy fiction", "Middle Earth", "Elves", "Hobbits", "Fiction", "English fiction", "Fiction", "Fiction", "Fiction"], Genre.fantasy),
        (["Poetry", "Italian poetry", "Poems", "Literature", "Fiction", "Medieval literature", "Literatura"], Genre.poetry),
        (["Fiction", "Brazilian fiction", "Religious", "Catholics"], Genre.fiction),
        (["Fiction", "Christian life", "Christianity", "Apologetics", "Devil"], Genre.religion),
        ([], Genre.other),
        (None, Genre.other),
    ],
    ids=["fantasia", "formacao", "religiao", "romance", "poesia", "ficcao-historica", "fantasia-vs-fiction",
         "poesia-vs-literatura", "romance-vs-religiao", "religiao-vs-fiction", "vazio", "nenhum"],
)
def test_classify(subjects, expected):
    assert classify(subjects) is expected


def test_search_returns_genre(client):
    doc = {"key": "/works/OL1W", "title": "The Hobbit", "subject": ["Fantasy", "dragons"]}
    app.dependency_overrides[open_library.get_client] = lambda: httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"docs": [doc]})))
    assert client.get("/books/search", params={"q": "hobbit"}).json()[0]["genre"] == "fantasy"


def test_add_and_edit_genre(client, book):
    b = client.post("/shelf", json={**book, "genre": "fiction"}).json()
    assert b["genre"] == "fiction"
    assert client.put(f"/shelf/{b['id']}", json={"genre": "poetry"}).json()["genre"] == "poetry"
    assert client.put(f"/shelf/{b['id']}", json={"genre": "sermao"}).status_code == 422


def test_insights_by_genre(client, book):
    a = client.post("/shelf", json={**book, "genre": "fantasy"}).json()
    b = client.post("/shelf", json={**book, "ol_key": "/works/OL2W", "genre": "fiction"}).json()
    client.put(f"/shelf/{a['id']}", json={"status": "read", "rating": 5})
    client.put(f"/shelf/{b['id']}", json={"status": "dropped"})
    res = client.get("/shelf/insights").json()
    assert res["liked_genres"] == [{"genre": "fantasy", "books": 1, "avg_rating": 5.0}]
    assert res["disliked_genres"] == [{"genre": "fiction", "dropped": 1, "low_rated": 0}]


def test_migration_adds_genre_column(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE books (id INTEGER PRIMARY KEY, ol_key VARCHAR(40))"))
    monkeypatch.setattr(db_module, "engine", engine)
    db_module._add_missing_columns()
    assert "genre" in {c["name"] for c in inspect(engine).get_columns("books")}
