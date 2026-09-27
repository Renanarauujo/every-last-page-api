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
    description="Estante pessoal de leitura com busca na Open Library.",
    version="1.0.0",
    lifespan=lifespan,
)

security.setup(app)

app.include_router(health.router)
app.include_router(books.router)
app.include_router(shelf.router)


@app.get("/", tags=["saude"])
def root():
    """Retorna o nome da API e o endereco da documentacao."""
    return {"nome": app.title, "docs": "/docs"}
