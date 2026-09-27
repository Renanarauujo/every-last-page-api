"""Rota de saude."""

from fastapi import APIRouter

router = APIRouter(tags=["saude"])


@router.get("/saude")
def health():
    """Informa que a API esta em funcionamento."""
    return {"status": "ok"}
