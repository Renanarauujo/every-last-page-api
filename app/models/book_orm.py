"""Tabela `livro`."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Book(Base):
    """Livro da estante."""

    __tablename__ = "livro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Dados da Open Library.
    ol_key: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column("titulo", String(300))
    author: Mapped[str | None] = mapped_column("autor", String(300))
    pages: Mapped[int | None] = mapped_column("total_paginas", Integer)
    cover_id: Mapped[int | None] = mapped_column("capa_id", Integer)

    # Dados do usuario.
    status: Mapped[str] = mapped_column(String(20))
    rating: Mapped[int | None] = mapped_column("nota", Integer)
    comment: Mapped[str | None] = mapped_column("comentario", String(500))

    # Datas preenchidas pela API.
    added_at: Mapped[datetime] = mapped_column("adicionado_em", DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column("iniciado_em", DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column("concluido_em", DateTime(timezone=True))
