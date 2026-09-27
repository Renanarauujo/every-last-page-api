"""Esquemas de entrada e saida do livro."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

TITLE_MAX = 300
COMMENT_MAX = 500
RATING_MIN = 1
RATING_MAX = 5

OL_KEY_RE = r"^/works/OL\d{1,12}W$"

# Nome do campo no codigo e nome correspondente no JSON.
JSON_NAMES = {
    "title": "titulo",
    "author": "autor",
    "pages": "total_paginas",
    "cover_id": "capa_id",
    "cover_url": "capa_url",
    "rating": "nota",
    "comment": "comentario",
    "added_at": "adicionado_em",
    "started_at": "iniciado_em",
    "finished_at": "concluido_em",
    "want": "quero_ler",
    "reading": "lendo",
    "read": "lidos",
    "dropped": "abandonados",
    "pages_read": "paginas_lidas",
    "avg_rating": "nota_media",
    "by_month": "lidos_por_mes",
    "month": "mes",
    "books": "livros",
}


class Schema(BaseModel):
    """Base dos esquemas, com os nomes do JSON em portugues."""

    model_config = ConfigDict(
        alias_generator=lambda name: JSON_NAMES.get(name, name),
        populate_by_name=True,
    )


class Status(str, Enum):
    """Status de leitura."""

    want = "quero_ler"
    reading = "lendo"
    read = "lido"
    dropped = "abandonado"


class Order(str, Enum):
    """Ordenacoes da listagem."""

    recent = "recentes"
    oldest = "antigos"
    title = "titulo"
    rating = "nota"


class BookIn(Schema):
    """Entrada do POST /estante. Campos adicionais sao ignorados."""

    model_config = ConfigDict(extra="ignore")

    ol_key: str = Field(pattern=OL_KEY_RE, examples=["/works/OL45804W"])
    title: str = Field(min_length=1, max_length=TITLE_MAX)
    author: str | None = Field(default=None, max_length=TITLE_MAX)
    pages: int | None = Field(default=None, ge=1)
    cover_id: int | None = Field(default=None, ge=1)


class BookEdit(Schema):
    """Entrada do PUT /estante/{id}. Apenas os campos enviados sao alterados."""

    model_config = ConfigDict(extra="forbid")

    status: Status | None = None
    rating: int | None = Field(default=None, ge=RATING_MIN, le=RATING_MAX)
    comment: str | None = Field(default=None, max_length=COMMENT_MAX)


class BookOut(Schema):
    """Livro da estante na resposta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ol_key: str
    title: str
    author: str | None
    pages: int | None
    cover_id: int | None
    status: Status
    rating: int | None
    comment: str | None
    added_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @field_validator("added_at", "started_at", "finished_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        """Atribui o fuso UTC as datas lidas sem fuso."""
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class MonthCount(Schema):
    """Livros concluidos e paginas em um mes."""

    month: str
    books: int
    pages: int = Field(alias="paginas")


class Summary(Schema):
    """Indicadores do painel."""

    total: int
    want: int
    reading: int
    read: int
    dropped: int
    pages_read: int
    avg_rating: float | None
    by_month: list[MonthCount]


class BookHit(Schema):
    """Resultado da busca na Open Library."""

    ol_key: str
    title: str
    author: str | None
    pages: int | None
    cover_id: int | None
    cover_url: str | None
