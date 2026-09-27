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


def _liked(books: list[Any], key: Callable[[Any], str | None], name: str) -> list[dict[str, Any]]:
    """Grupos (autor ou tipo) com nota media a partir de LIKED_MIN, mais lidos primeiro."""
    ratings, count = defaultdict(list), defaultdict(int)
    for b in books:
        group = key(b)
        if not group:
            continue
        count[group] += 1
        if b.rating is not None:
            ratings[group].append(b.rating)
    out = [{name: g, "books": count[g], "avg_rating": round(sum(r) / len(r), DIGITS)}
           for g, r in ratings.items() if sum(r) / len(r) >= LIKED_MIN]
    return sorted(out, key=lambda a: (-a["books"], -a["avg_rating"], a[name]))[:TOP]


def _disliked(books: list[Any], key: Callable[[Any], str | None], name: str) -> list[dict[str, Any]]:
    """Grupos (autor ou tipo) com livro abandonado ou nota ate DISLIKED_MAX."""
    marks = defaultdict(lambda: {"dropped": 0, "low_rated": 0})
    for b in books:
        group = key(b)
        if not group:
            continue
        if b.status == Status.dropped.value:
            marks[group]["dropped"] += 1
        if b.rating is not None and b.rating <= DISLIKED_MAX:
            marks[group]["low_rated"] += 1
    out = [{name: g, **m} for g, m in marks.items() if m["dropped"] or m["low_rated"]]
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
    """Livro de maior nota; em empate, o concluido mais recentemente."""
    rated = [b for b in books if b.rating is not None]
    if not rated:
        return None
    best = max(rated, key=lambda b: (b.rating, b.finished_at or b.added_at))
    return {"title": best.title, "author": author(best), "rating": best.rating}
