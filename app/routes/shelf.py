"""Rotas da estante."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.book import BookEdit, BookIn, BookOut, Order, Status, Summary
from app.models.book_orm import Book
from app.services import reading

router = APIRouter(prefix="/shelf", tags=["shelf"])

NOT_FOUND = "Livro nao encontrado na estante."
DUPLICATE = "Este livro ja esta na estante."

_ORDERS = {
    Order.recent: [Book.added_at.desc(), Book.id.desc()],
    Order.oldest: [Book.added_at.asc(), Book.id.asc()],
    Order.title: [func.lower(Book.title).asc()],
    Order.rating: [Book.rating.desc().nulls_last(), Book.id.desc()],
}


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def add(data: BookIn, db: Session = Depends(get_db)):
    """Add a book to the shelf. Returns 409 if it is already there."""
    if db.scalar(select(Book.id).where(Book.ol_key == data.ol_key)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=DUPLICATE)

    book = Book(**data.model_dump())
    reading.init(book, reading.now())
    db.add(book)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail=DUPLICATE)
    return book


@router.get("", response_model=list[BookOut])
def list_all(
    state: Status | None = Query(None, alias="status"),
    order: Order = Order.recent,
    db: Session = Depends(get_db),
):
    """List the shelf, filtered by status and ordered."""
    query = select(Book).order_by(*_ORDERS[order])
    if state is not None:
        query = query.where(Book.status == state.value)
    return db.scalars(query).all()


# Declarada antes de /{id} para nao ser tratada como id.
@router.get("/summary", response_model=Summary)
def summary(db: Session = Depends(get_db)):
    """Return the dashboard numbers."""
    books = db.scalars(select(Book)).all()
    return Summary(**reading.summary(books, reading.now()))


@router.get("/{id}", response_model=BookOut)
def get(id: int, db: Session = Depends(get_db)):
    """Return a book from the shelf."""
    return _find(db, id)


@router.put("/{id}", response_model=BookOut)
def update(id: int, data: BookEdit, db: Session = Depends(get_db)):
    """Update status, rating and comment."""
    book = _find(db, id)
    reading.update(book, data.model_dump(exclude_unset=True), reading.now())
    db.commit()
    return book


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(id: int, db: Session = Depends(get_db)):
    """Remove a book from the shelf."""
    db.delete(_find(db, id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _find(db: Session, id: int) -> Book:
    """Retorna o livro pelo id ou responde 404."""
    book = db.get(Book, id)
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return book
