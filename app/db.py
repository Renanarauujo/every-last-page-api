"""Conexao com o banco de dados."""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shelf.db")

_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_ARGS)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base dos modelos ORM."""


def get_db() -> Iterator[Session]:
    """Fornece uma sessao por requisicao."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Cria as tabelas inexistentes."""
    from app.models import book_orm  # noqa: F401

    Base.metadata.create_all(engine)
