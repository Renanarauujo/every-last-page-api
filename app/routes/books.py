"""Rota de busca de livros na Open Library."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.book import BookHit
from app.security import search_limit
from app.services import open_library

router = APIRouter(prefix="/books", tags=["books"])

LIMIT = 10
LIMIT_MAX = 20


@router.get("/search", response_model=list[BookHit], dependencies=[Depends(search_limit)])
def search(
    q: str = Query(min_length=2, max_length=100, description="Title, author or ISBN"),
    limit: int = Query(LIMIT, ge=1, le=LIMIT_MAX),
    client: httpx.Client = Depends(open_library.get_client),
):
    """Search books on Open Library. Returns 502 when Open Library fails."""
    try:
        return open_library.search(client, q.strip(), limit)
    except open_library.Unavailable:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="A Open Library nao respondeu. Tente de novo em instantes.",
        )
