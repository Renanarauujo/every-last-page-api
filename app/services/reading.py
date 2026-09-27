"""Regras de status e resumo da estante.

As datas registram o momento da troca de status. Reenviar o status atual nao altera datas.

1. Todo livro entra como `quero_ler`, sem datas de leitura.
2. `quero_ler`: `iniciado_em` e `concluido_em` sao apagadas.
3. `lendo`: `iniciado_em` recebe a data da troca e `concluido_em` e apagada.
4. `lido`: `concluido_em` recebe a data da troca; `iniciado_em` tambem, se vazia.
5. `abandonado`: `concluido_em` recebe a data do abandono e `iniciado_em` e mantida.
"""

from datetime import datetime, timezone
from typing import Any

from app.models.book import Status

MONTHS = 6
DIGITS = 1


def now() -> datetime:
    """Retorna a data e hora atuais em UTC."""
    return datetime.now(timezone.utc)


def init(book: Any, at: datetime) -> None:
    """Aplica a regra 1."""
    book.status = Status.want.value
    book.added_at = at


def update(book: Any, changes: dict[str, Any], at: datetime) -> None:
    """Aplica uma atualizacao parcial com as regras 2 a 5."""
    for field in ("rating", "comment"):
        if field in changes:
            setattr(book, field, changes[field])

    if changes.get("status") is not None:
        _set_status(book, Status(changes["status"]), at)


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
