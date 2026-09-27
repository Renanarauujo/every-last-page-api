"""Rota de busca de livros na Open Library."""

import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.book import BookHit, Language, SearchField, SearchSort
from app.security import search_limit
from app.services import open_library

router = APIRouter(prefix="/books", tags=["books"])

LIMIT = 20
LIMIT_MAX = 40
ISBN_RE = re.compile(r"^(\d{9}[\dX]|\d{13})$")


@router.get("/search", response_model=list[BookHit], dependencies=[Depends(search_limit)])
def search(
    q: str = Query(min_length=2, max_length=100, description="Title, author or ISBN"),
    limit: int = Query(LIMIT, ge=1, le=LIMIT_MAX),
    field: SearchField = SearchField.all,
    language: Language = Language.any,
    sort: SearchSort = SearchSort.relevance,
    client: httpx.Client = Depends(open_library.get_client),
):
    """Search books on Open Library. Returns 502 when Open Library fails."""
    q = q.strip()
    if field is SearchField.isbn:
        q = q.replace("-", "").replace(" ", "").upper()
        if not ISBN_RE.match(q):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ISBN invalido.")
    try:
        return open_library.search(client, q, limit, field, language, sort)
    except open_library.Unavailable:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="A Open Library nao respondeu. Tente de novo em instantes.",
        )
