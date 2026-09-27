"""Perfil de leitura: tipos e autores que o usuario gosta e evita, a partir dos livros ja iniciados."""

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from app.models.book import Status

STARTED = {Status.reading.value, Status.read.value, Status.dropped.value}
LIKED_MIN = 4
DISLIKED_MAX = 2
TOP = 3
PERCENT = 100
DIGITS = 1


def author(book: Any) -> str | None:
    """Retorna o primeiro autor do livro."""
    name = (book.author or "").split(",")[0].strip()
    return name or None


def insights(books: list[Any]) -> dict[str, Any]:
    """Calcula o perfil de leitura dos livros lidos, em leitura ou abandonados."""
    started = [b for b in books if b.status in STARTED]
    done = [b for b in started if b.status == Status.read.value]
    dropped = [b for b in started if b.status == Status.dropped.value]
    liked = [b for b in started if b.rating is not None and b.rating >= LIKED_MIN]
    return {
        "books": len(started),
        "liked_genres": _liked(started, genre, "genre"),
        "disliked_genres": _disliked(started, genre, "genre"),
        "liked_authors": _liked(started, author, "author"),
        "disliked_authors": _disliked(started, author, "author"),
        "liked_pages": _avg([b.pages for b in liked if b.pages]),
        "dropped_pages": _avg([b.pages for b in dropped if b.pages]),
        "completion_rate": round(len(done) / (len(done) + len(dropped)) * PERCENT) if done or dropped else None,
        "avg_days": _avg([_days(b) for b in done if _days(b)]),
        "pages_per_day": _pace(done),
        "favorite": _favorite(started),
    }


def _groups(books: list[Any], key: Callable[[Any], str | None]) -> dict[str, dict[str, Any]]:
    """Agrupa por autor ou tipo: quantidade, notas, bem avaliados, abandonos e notas baixas."""
    groups = defaultdict(lambda: {"books": 0, "ratings": [], "good": 0, "dropped": 0, "low_rated": 0})
    for b in books:
        name = key(b)
        if not name:
            continue
        g = groups[name]
        g["books"] += 1
        if b.rating is not None:
            g["ratings"].append(b.rating)
            g["good"] += b.rating >= LIKED_MIN
            g["low_rated"] += b.rating <= DISLIKED_MAX
        g["dropped"] += b.status == Status.dropped.value
    return groups


def _bad(g: dict[str, Any]) -> int:
    """Abandonos mais notas baixas."""
    return g["dropped"] + g["low_rated"]


def _liked(books: list[Any], key: Callable[[Any], str | None], name: str) -> list[dict[str, Any]]:
    """Grupos com media a partir de LIKED_MIN e mais bem avaliados do que abandonos e notas baixas."""
    out = [{name: n, "books": g["books"], "avg_rating": round(sum(g["ratings"]) / len(g["ratings"]), DIGITS)}
           for n, g in _groups(books, key).items()
           if g["ratings"] and sum(g["ratings"]) / len(g["ratings"]) >= LIKED_MIN and g["good"] > _bad(g)]
    return sorted(out, key=lambda a: (-a["books"], -a["avg_rating"], a[name]))[:TOP]


def _disliked(books: list[Any], key: Callable[[Any], str | None], name: str) -> list[dict[str, Any]]:
    """Grupos com abandonos e notas baixas em numero igual ou maior que os bem avaliados."""
    out = [{name: n, "dropped": g["dropped"], "low_rated": g["low_rated"]}
           for n, g in _groups(books, key).items() if _bad(g) and _bad(g) >= g["good"]]
    return sorted(out, key=lambda a: (-(a["dropped"] + a["low_rated"]), a[name]))[:TOP]


def genre(book: Any) -> str | None:
    """Retorna o tipo do livro, se conhecido."""
    return getattr(book, "genre", None) or None


def _days(book: Any) -> int | None:
    """Dias entre o inicio e a conclusao, no minimo 1."""
    if not book.started_at or not book.finished_at:
        return None
    return max(1, (book.finished_at.date() - book.started_at.date()).days)


def _pace(books: list[Any]) -> float | None:
    """Paginas por dia nos livros lidos com paginas e datas."""
    pairs = [(b.pages, _days(b)) for b in books if b.pages and _days(b)]
    if not pairs:
        return None
    return round(sum(p for p, _ in pairs) / sum(d for _, d in pairs), DIGITS)


def _avg(values: list[int]) -> int | None:
    """Media arredondada, ou None se nao houver valores."""
    return round(sum(values) / len(values)) if values else None


def _favorite(books: list[Any]) -> dict[str, Any] | None:
    """Livro lido de maior nota com mais paginas por dia; sem paginas ou datas, o concluido mais recente."""
    read = [b for b in books if b.status == Status.read.value and b.rating is not None]
    if not read:
        return None
    top = max(b.rating for b in read)
    best_rated = [b for b in read if b.rating == top]
    timed = [b for b in best_rated if b.pages and _days(b)]
    if timed:
        best = max(timed, key=lambda b: (b.pages / _days(b), -_days(b)))
    else:
        best = max(best_rated, key=lambda b: b.finished_at or b.added_at)
    days = _days(best)
    return {
        "title": best.title,
        "author": author(best),
        "rating": best.rating,
        "pages": best.pages,
        "days": days,
        "pages_per_day": round(best.pages / days, DIGITS) if best.pages and days else None,
    }
