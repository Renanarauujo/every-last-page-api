"""Testes da busca, com a Open Library simulada."""

import httpx
import pytest

from app.main import app
from app.security import SEARCH_LIMIT
from app.services import open_library

OL_RESPONSE = {
    "numFound": 3,
    "docs": [
        {
            "key": "/works/OL1062599W",
            "title": "Dom Casmurro",
            "author_name": ["Machado de Assis", "Outro", "Terceiro"],
            "number_of_pages_median": 256,
            "cover_i": 8231856,
        },
        {"key": "/works/OL2W", "title": "Sem capa nem paginas"},
        {"key": "/authors/OL1A", "title": "Nao e uma obra"},
    ],
}


def fake_ol(handler):
    """Substitui o cliente HTTP da rota por um cliente simulado."""
    calls = []

    def handle(req):
        calls.append(req)
        return handler(req)

    def fake_client():
        with httpx.Client(transport=httpx.MockTransport(handle)) as c:
            yield c

    app.dependency_overrides[open_library.get_client] = fake_client
    return calls


def test_search(client):
    calls = fake_ol(lambda r: httpx.Response(200, json=OL_RESPONSE))
    res = client.get("/books/search", params={"q": "dom casmurro", "limit": 5})

    assert res.status_code == 200
    assert res.json() == [
        {
            "ol_key": "/works/OL1062599W",
            "title": "Dom Casmurro",
            "author": "Machado de Assis, Outro",
            "pages": 256,
            "cover_id": 8231856,
            "cover_url": "https://covers.openlibrary.org/b/id/8231856-M.jpg",
            "genre": "other",
        },
        {
            "ol_key": "/works/OL2W",
            "title": "Sem capa nem paginas",
            "author": None,
            "pages": None,
            "cover_id": None,
            "cover_url": None,
            "genre": "other",
        },
    ]
    assert calls[0].url.params["q"] == "dom casmurro"
    assert calls[0].url.params["limit"] == "5"


@pytest.mark.parametrize(
    "fail",
    [
        lambda r: httpx.Response(503),
        lambda r: httpx.Response(200, text="<html>nao e json</html>"),
        lambda r: (_ for _ in ()).throw(httpx.ReadTimeout("timeout", request=r)),
        lambda r: (_ for _ in ()).throw(httpx.ConnectError("offline", request=r)),
    ],
    ids=["503", "html", "timeout", "offline"],
)
def test_search_502(client, fail):
    fake_ol(fail)
    res = client.get("/books/search", params={"q": "dom casmurro"})
    assert res.status_code == 502
    assert res.json()["detail"] == "A Open Library nao respondeu. Tente de novo em instantes."


def test_search_invalid(client):
    fake_ol(lambda r: httpx.Response(200, json=OL_RESPONSE))
    assert client.get("/books/search", params={"q": "a"}).status_code == 422
    assert client.get("/books/search", params={"q": "dom", "limit": 50}).status_code == 422
    assert client.get("/books/search", params={"q": "dom", "field": "year"}).status_code == 422
    assert client.get("/books/search", params={"q": "dom", "language": "xx"}).status_code == 422
    assert client.get("/books/search", params={"q": "123", "field": "isbn"}).status_code == 422


def test_search_429(client):
    fake_ol(lambda r: httpx.Response(200, json={"docs": []}))
    for _ in range(SEARCH_LIMIT):
        assert client.get("/books/search", params={"q": "dom"}).status_code == 200
    res = client.get("/books/search", params={"q": "dom"})
    assert res.status_code == 429
    assert int(res.headers["Retry-After"]) > 0


def test_search_normalizes_accents(client):
    doc = {"key": "/works/OL3W", "title": "Grande sertão", "author_name": ["João Guimarães Rosa"]}
    fake_ol(lambda r: httpx.Response(200, json={"docs": [doc]}))
    res = client.get("/books/search", params={"q": "sertao"}).json()
    assert res[0]["author"] == "João Guimarães Rosa"


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"q": "machado"}, {"q": "machado"}),
        ({"q": "machado", "field": "author"}, {"author": "machado"}),
        ({"q": "dom", "field": "title", "language": "por", "sort": "new"}, {"title": "dom", "language": "por", "sort": "new"}),
        ({"q": "978-85-359-0277-7", "field": "isbn"}, {"q": "isbn:9788535902777"}),
    ],
    ids=["all", "author", "title-por-new", "isbn"],
)
def test_search_filters(client, params, expected):
    calls = fake_ol(lambda r: httpx.Response(200, json={"docs": []}))
    assert client.get("/books/search", params=params).status_code == 200
    sent = dict(calls[0].url.params)
    for key, value in expected.items():
        assert sent[key] == value
