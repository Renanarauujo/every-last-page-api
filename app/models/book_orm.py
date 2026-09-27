"""Tabela `books`."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Book(Base):
    """Livro da estante."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Dados da Open Library.
    ol_key: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    author: Mapped[str | None] = mapped_column(String(300))
    pages: Mapped[int | None] = mapped_column(Integer)
    cover_id: Mapped[int | None] = mapped_column(Integer)

    # Dados do usuario.
    status: Mapped[str] = mapped_column(String(20))
    rating: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(String(500))

    # Datas preenchidas pela API.
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
