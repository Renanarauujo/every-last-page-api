"""Regras de status e resumo da estante.

As datas registram o momento da troca de status. Reenviar o status atual nao altera datas.

1. Todo livro entra como `want`, sem datas de leitura.
2. `want`: `started_at` e `finished_at` sao apagadas.
3. `reading`: `started_at` recebe a data da troca e `finished_at` e apagada.
4. `read`: `finished_at` recebe a data da troca; `started_at` tambem, se vazia.
5. `dropped`: `finished_at` recebe a data do abandono e `started_at` e mantida.
6. Datas enviadas no PUT substituem as da regra, se forem coerentes com o status.
"""

from datetime import date, datetime, timezone
from typing import Any

from app.models.book import Status

MONTHS = 6
DIGITS = 1
NOON = 12


class InvalidDates(ValueError):
    """Datas incoerentes com o status ou entre si."""


def now() -> datetime:
    """Retorna a data e hora atuais em UTC."""
    return datetime.now(timezone.utc)


def init(book: Any, at: datetime) -> None:
    """Aplica a regra 1."""
    book.status = Status.want.value
    book.added_at = at


def update(book: Any, changes: dict[str, Any], at: datetime) -> None:
    """Aplica uma atualizacao parcial com as regras 2 a 6. Lanca `InvalidDates` na regra 6."""
    for field in ("rating", "comment"):
        if field in changes:
            setattr(book, field, changes[field])

    if changes.get("status") is not None:
        _set_status(book, Status(changes["status"]), at)

    dates = [f for f in ("started_at", "finished_at") if f in changes]
    for field in dates:
        setattr(book, field, _noon(changes[field]))
    if dates:
        _check_dates(book, at)


def _noon(day: date | None) -> datetime | None:
    """Converte uma data em meio-dia UTC, para nao mudar de dia no fuso do usuario."""
    return datetime(day.year, day.month, day.day, NOON, tzinfo=timezone.utc) if day else None


def _check_dates(book: Any, at: datetime) -> None:
    """Valida as datas informadas contra o status e entre si."""
    started, finished = book.started_at, book.finished_at
    if book.status == Status.want.value and (started or finished):
        raise InvalidDates("Livro em Quero ler nao tem datas de leitura.")
    if book.status == Status.reading.value and finished:
        raise InvalidDates("Livro em Lendo nao tem data de conclusao.")
    if any(d and d.date() > at.date() for d in (started, finished)):
        raise InvalidDates("A data nao pode estar no futuro.")
    if started and finished and finished.date() < started.date():
        raise InvalidDates("A conclusao nao pode ser anterior ao inicio.")


def _set_status(book: Any, new: Status, at: datetime) -> None:
    """Altera o status e as datas correspondentes."""
    if book.status == new.value:
        return
    book.status = new.value

    if new is Status.want:
        book.started_at = None
        book.finished_at = None
    elif new is Status.reading:
        book.started_at = at
        book.finished_at = None
    elif new is Status.read:
        book.finished_at = at
        if book.started_at is None:
            book.started_at = at
    else:
        book.finished_at = at


def summary(books: list[Any], at: datetime) -> dict[str, Any]:
    """Calcula os indicadores do painel para os ultimos MONTHS meses."""
    count = {s.value: 0 for s in Status}
    for book in books:
        count[book.status] = count.get(book.status, 0) + 1

    done = [b for b in books if b.status == Status.read.value]
    ratings = [b.rating for b in books if b.rating is not None]

    months = {m: {"month": m, "books": 0} for m in _months(at)}
    for book in done:
        key = book.finished_at.strftime("%Y-%m") if book.finished_at else None
        if key in months:
            months[key]["books"] += 1

    return {
        "total": len(books),
        "want": count[Status.want.value],
        "reading": count[Status.reading.value],
        "read": len(done),
        "dropped": count[Status.dropped.value],
        "pages_read": sum(b.pages or 0 for b in done),
        "avg_rating": round(sum(ratings) / len(ratings), DIGITS) if ratings else None,
        "by_month": list(months.values()),
    }


def _months(at: datetime, n: int = MONTHS) -> list[str]:
    """Retorna os `n` meses ate `at`, em ordem crescente, no formato AAAA-MM."""
    year, month = at.year, at.month
    out = []
    for _ in range(n):
        out.append(f"{year:04d}-{month:02d}")
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    return list(reversed(out))
