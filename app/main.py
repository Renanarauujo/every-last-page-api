"""Aplicacao FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import security
from app.db import create_tables
from app.routes import books, health, shelf


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Cria as tabelas na inicializacao."""
    create_tables()
    yield


app = FastAPI(
    title="Every Last Page API",
    description="Personal reading shelf with Open Library search.",
    version="1.0.0",
    lifespan=lifespan,
)

security.setup(app)

app.include_router(health.router)
app.include_router(books.router)
app.include_router(shelf.router)

