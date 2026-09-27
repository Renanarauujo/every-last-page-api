"""Classificacao do tipo do livro a partir dos assuntos da Open Library."""

from collections import Counter

from app.models.book import Genre

# Ordem de prioridade: cada assunto vota no primeiro tipo cujas palavras aparecem nele.
# "Fantasy fiction" vota em fantasia antes de ficcao; "Historical fiction" vota em ficcao antes de historia.
RULES: list[tuple[Genre, tuple[str, ...]]] = [
    (Genre.fantasy, ("fantasy", "middle earth", "middle-earth", "hobbit", "elves", "dragon", "wizard", "magic", "fairy")),
    (Genre.science_fiction, ("science fiction", "dystopia", "space opera", "robots")),
    (Genre.mystery, ("mystery", "detective", "thriller", "suspense", "crime fiction")),
    (Genre.poetry, ("poetry", "poems", "poem", "verse")),
    (Genre.fiction, ("fiction", "novel", "novela", "romance", "literature", "literatura", "satire", "classics", "criticism", "short stories")),
    (Genre.education, ("rhetoric", "grammar", "logic", "critical thinking", "reading", "study and teaching", "education", "learning", "language arts", "intellectual life")),
    (Genre.religion, ("christian", "religio", "theolog", "spiritual", "church", "catholic", "apologet", "saint", "bible", "faith", "devil", "prayer", "god")),
    (Genre.philosophy, ("philosoph", "ethics", "metaphysic", "stoic")),
    (Genre.biography, ("biograph", "memoir", "correspondence", "letters", "diaries")),
    (Genre.history, ("history", "historical", "war")),
]
TIE_ORDER = [genre for genre, _ in RULES]
FICTION_KINDS = (Genre.fantasy, Genre.science_fiction, Genre.mystery, Genre.poetry)
# Um subgenero de ficcao vence o "Fiction" generico com mais da metade dos votos dele.
FICTION_WEIGHT = 0.5


def _vote(subject: str) -> Genre | None:
    """Retorna o tipo em que o assunto vota, ou None se nao casar com nenhum."""
    text = subject.lower()
    for genre, words in RULES:
        if any(w in text for w in words):
            return genre
    return None


def classify(subjects: list[str] | None) -> Genre:
    """Classifica o livro pelos votos dos assuntos, em duas etapas: subgenero contra ficcao generica, depois ficcao contra nao ficcao."""
    votes = Counter(g for g in map(_vote, subjects or []) if g)
    if not votes:
        return Genre.other
    kind = _best(votes, FICTION_KINDS)
    fiction = votes[Genre.fiction]
    if kind and votes[kind] > fiction * FICTION_WEIGHT:
        return kind
    block = fiction + sum(votes[k] for k in FICTION_KINDS)
    other = _best(votes, [g for g in TIE_ORDER if g not in FICTION_KINDS and g is not Genre.fiction])
    if other and votes[other] > block:
        return other
    return Genre.fiction if fiction else kind or other


def _best(votes: Counter, genres: list[Genre] | tuple[Genre, ...]) -> Genre | None:
    """Tipo mais votado entre os informados; empate segue a ordem das regras."""
    present = [g for g in genres if votes[g]]
    if not present:
        return None
    top = max(votes[g] for g in present)
    return next(g for g in TIE_ORDER if g in present and votes[g] == top)
