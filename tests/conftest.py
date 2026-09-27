"""Fixtures dos testes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import book_orm  # noqa: F401
from app.security import search_limit

BOOK = {
    "ol_key": "/works/OL45804W",
    "titulo": "Dom Casmurro",
    "autor": "Machado de Assis",
    "total_paginas": 256,
    "capa_id": 8231856,
}


@pytest.fixture
def client():
    """Cliente de teste com banco SQLite em memoria, recriado a cada teste."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = test_db
    search_limit.reset()
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def book():
    """Corpo valido de POST /estante."""
    return dict(BOOK)
