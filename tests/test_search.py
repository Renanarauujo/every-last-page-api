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
    res = client.get("/livros/busca", params={"q": "dom casmurro", "limite": 5})

    assert res.status_code == 200
    assert res.json() == [
        {
            "ol_key": "/works/OL1062599W",
            "titulo": "Dom Casmurro",
            "autor": "Machado de Assis, Outro",
            "total_paginas": 256,
            "capa_id": 8231856,
            "capa_url": "https://covers.openlibrary.org/b/id/8231856-M.jpg",
        },
        {
            "ol_key": "/works/OL2W",
            "titulo": "Sem capa nem paginas",
            "autor": None,
            "total_paginas": None,
            "capa_id": None,
            "capa_url": None,
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
    res = client.get("/livros/busca", params={"q": "dom casmurro"})
    assert res.status_code == 502
    assert res.json()["detail"] == "A Open Library nao respondeu. Tente de novo em instantes."


def test_search_invalid(client):
    fake_ol(lambda r: httpx.Response(200, json=OL_RESPONSE))
    assert client.get("/livros/busca", params={"q": "a"}).status_code == 422
    assert client.get("/livros/busca", params={"q": "dom", "limite": 50}).status_code == 422


def test_search_429(client):
    fake_ol(lambda r: httpx.Response(200, json={"docs": []}))
    for _ in range(SEARCH_LIMIT):
        assert client.get("/livros/busca", params={"q": "dom"}).status_code == 200
    res = client.get("/livros/busca", params={"q": "dom"})
    assert res.status_code == 429
    assert int(res.headers["Retry-After"]) > 0
