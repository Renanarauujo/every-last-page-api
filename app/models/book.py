"""Esquemas de entrada e saida do livro."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

TITLE_MAX = 300
COMMENT_MAX = 500
RATING_MIN = 1
RATING_MAX = 5

OL_KEY_RE = r"^/works/OL\d{1,12}W$"


class Status(str, Enum):
    """Reading status."""

    want = "want"
    reading = "reading"
    read = "read"
    dropped = "dropped"


class Order(str, Enum):
    """Shelf ordering."""

    recent = "recent"
    oldest = "oldest"
    title = "title"
    rating = "rating"


class BookIn(BaseModel):
    """Body of POST /shelf. Extra fields are ignored."""

    model_config = ConfigDict(extra="ignore")

    ol_key: str = Field(pattern=OL_KEY_RE, examples=["/works/OL45804W"])
    title: str = Field(min_length=1, max_length=TITLE_MAX)
    author: str | None = Field(default=None, max_length=TITLE_MAX)
    pages: int | None = Field(default=None, ge=1)
    cover_id: int | None = Field(default=None, ge=1)


class BookEdit(BaseModel):
    """Body of PUT /shelf/{id}. Only the fields sent are changed."""

    model_config = ConfigDict(extra="forbid")

    status: Status | None = None
    rating: int | None = Field(default=None, ge=RATING_MIN, le=RATING_MAX)
    comment: str | None = Field(default=None, max_length=COMMENT_MAX)


class BookOut(BaseModel):
    """Book on the shelf."""

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


class MonthCount(BaseModel):
    """Books read in a month."""

    month: str
    books: int


class Summary(BaseModel):
    """Dashboard numbers."""

    total: int
    want: int
    reading: int
    read: int
    dropped: int
    pages_read: int
    avg_rating: float | None
    by_month: list[MonthCount]


class BookHit(BaseModel):
    """Open Library search result."""

    ol_key: str
    title: str
    author: str | None
    pages: int | None
    cover_id: int | None
    cover_url: str | None
