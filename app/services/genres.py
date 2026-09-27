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


def _vote(subject: str) -> Genre | None:
    """Retorna o tipo em que o assunto vota, ou None se nao casar com nenhum."""
    text = subject.lower()
    for genre, words in RULES:
        if any(w in text for w in words):
            return genre
    return None


def classify(subjects: list[str] | None) -> Genre:
    """Classifica o livro pelo tipo mais votado entre os assuntos; empate segue a ordem das regras."""
    votes = Counter(g for g in map(_vote, subjects or []) if g)
    if not votes:
        return Genre.other
    top = max(votes.values())
    return next(g for g in TIE_ORDER if votes.get(g) == top)
