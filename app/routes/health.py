"""Rota de saude."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Report that the API is running."""
    return {"status": "ok"}
