"""Cliente da Search API da Open Library."""

import re
from collections.abc import Iterator
from typing import Any

import httpx

from app.models.book import OL_KEY_RE, TITLE_MAX, BookHit

SEARCH_URL = "https://openlibrary.org/search.json"
COVER_URL = "https://covers.openlibrary.org/b/id/{id}-M.jpg"
USER_AGENT = "EveryLastPage/1.0 (+https://github.com/Renanarauujo/every-last-page-api)"
TIMEOUT = 8.0
FIELDS = "key,title,author_name,number_of_pages_median,cover_i"
MAX_AUTHORS = 2

_KEY = re.compile(OL_KEY_RE)


class Unavailable(Exception):
    """Falha, demora ou resposta invalida da Open Library."""


def get_client() -> Iterator[httpx.Client]:
    """Fornece um cliente HTTP por requisicao."""
    with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
        yield client


def search(client: httpx.Client, q: str, limit: int) -> list[BookHit]:
    """Busca livros na Open Library. Lanca `Unavailable` em caso de falha."""
    try:
        res = client.get(SEARCH_URL, params={"q": q, "fields": FIELDS, "limit": limit})
        res.raise_for_status()
        docs = res.json().get("docs", [])
    except (httpx.HTTPError, ValueError, AttributeError) as err:
        raise Unavailable(str(err)) from err

    return [hit for doc in docs if (hit := _parse(doc)) is not None]


def _parse(doc: Any) -> BookHit | None:
    """Converte um documento da Open Library. Descarta o que nao for obra valida."""
    if not isinstance(doc, dict):
        return None
    key, title = doc.get("key"), doc.get("title")
    if not isinstance(key, str) or not _KEY.match(key) or not title:
        return None

    authors = doc.get("author_name") or []
    cover = doc.get("cover_i")
    cover = cover if isinstance(cover, int) and cover > 0 else None
    pages = doc.get("number_of_pages_median")

    return BookHit(
        ol_key=key,
        title=_fix(str(title))[:TITLE_MAX],
        author=_fix(", ".join(map(str, authors[:MAX_AUTHORS]))) or None,
        pages=pages if isinstance(pages, int) and pages > 0 else None,
        cover_id=cover,
        cover_url=COVER_URL.format(id=cover) if cover else None,
    )


def _fix(text: str) -> str:
    """Corrige texto UTF-8 que a Open Library entrega decodificado como Latin-1."""
    if "Ã" not in text and "Â" not in text:
        return text
    for encoding in ("latin-1", "cp1252"):
        try:
            return text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
    return text
