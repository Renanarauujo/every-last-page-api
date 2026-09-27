# Every Last Page API

**MVP PUC-Rio · Every Last Page · Renan Araújo**

API REST da estante pessoal de leitura do **Every Last Page**. Guarda os livros do usuário em
SQLite, aplica as regras de status da leitura e busca livros na [Open Library](https://openlibrary.org),
devolvendo os dados já tratados para o front.

Faz parte de dois repositórios:

- [every-last-page-front](https://github.com/Renanarauujo/every-last-page-front): a interface
  e o `docker-compose.yml` que sobe tudo.
- **every-last-page-api** (este): a API.

## Tecnologias

- Python 3.11 e [FastAPI](https://fastapi.tiangolo.com), com documentação Swagger automática
- [Pydantic](https://docs.pydantic.dev) para validar entrada e saída
- [SQLAlchemy](https://www.sqlalchemy.org) com SQLite
- [httpx](https://www.python-httpx.org) para chamar a Open Library
- pytest para os testes

## Como executar

### Com Docker (recomendado)

A forma completa, com o front, está no repositório
[every-last-page-front](https://github.com/Renanarauujo/every-last-page-front): clone os dois
lado a lado e rode `docker compose up --build` na pasta do front.

Para subir só a API:

```bash
docker build -t every-last-page-api .
docker run --rm -p 8000:8000 -v shelf-data:/data every-last-page-api
```

### Sem Docker

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # Linux e macOS
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API fica em `http://localhost:8000` e o Swagger em `http://localhost:8000/docs`.

### Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./shelf.db` | Endereço do banco. No container: `sqlite:////data/shelf.db` |
| `CORS_ORIGINS` | `http://localhost:8080,http://127.0.0.1:8080` | Origens do front liberadas no CORS, separadas por vírgula |

Nenhuma chave é necessária: a Open Library é pública e não pede cadastro.

## Rotas

| Método | Rota | Descrição | Respostas |
|---|---|---|---|
| GET | `/health` | Informa que a API está no ar | 200 |
| GET | `/books/search?q=&limit=` | Busca livros na Open Library | 200, 422, 429, 502 |
| POST | `/shelf` | Adiciona um livro à estante | 201, 409, 422 |
| GET | `/shelf?status=&order=` | Lista a estante, com filtro e ordenação | 200, 422 |
| GET | `/shelf/summary` | Números do painel | 200 |
| GET | `/shelf/insights` | Perfil de leitura: tipos e autores preferidos e evitados (top 3), tamanhos, ritmo e favorito | 200 |
| PUT | `/shelf/{id}` | Atualiza status, nota, comentário e datas de leitura | 200, 404, 422 |
| DELETE | `/shelf/{id}` | Remove um livro | 204, 404 |

A documentação interativa, com os esquemas de cada corpo, está em `/docs`.

### Exemplos

Adicionar um livro (o corpo é um item de `GET /books/search`):

```http
POST /shelf
Content-Type: application/json

{"ol_key": "/works/OL1003040W", "title": "Dom Casmurro", "author": "Machado de Assis", "pages": 268, "cover_id": 647501}
```

Marcar como lido, com nota e comentário:

```http
PUT /shelf/1
Content-Type: application/json

{"status": "read", "rating": 5, "comment": "Capitu traiu?"}
```

Resposta:

```json
{
  "id": 1,
  "ol_key": "/works/OL1003040W",
  "title": "Dom Casmurro",
  "author": "Machado de Assis",
  "pages": 268,
  "cover_id": 647501,
  "status": "read",
  "rating": 5,
  "comment": "Capitu traiu?",
  "added_at": "2026-09-27T13:16:43Z",
  "started_at": "2026-09-27T13:16:43Z",
  "finished_at": "2026-09-27T13:16:43Z"
}
```

## Regras de status

Status possíveis: `want` (quero ler), `reading` (lendo), `read` (lido) e `dropped` (abandonado).
As datas registram o momento da troca de status; reenviar o status atual não altera nada.

1. Todo livro entra como `want`, sem datas de leitura.
2. `want`: `started_at` e `finished_at` são apagadas.
3. `reading`: `started_at` recebe a data da troca e `finished_at` é apagada.
4. `read`: `finished_at` recebe a data da troca; `started_at` também, se estiver vazia.
5. `dropped`: `finished_at` recebe a data do abandono e `started_at` é mantida.
6. `started_at` e `finished_at` também podem ser enviadas no PUT (`AAAA-MM-DD`) e substituem as da
   regra. A API recusa com 422 data no futuro, conclusão antes do início, datas em `want` e
   conclusão em `reading`.

Cada livro tem um tipo (`genre`: `fantasy`, `science_fiction`, `fiction`, `mystery`, `poetry`,
`education`, `religion`, `philosophy`, `biography`, `history`, `other`), calculado pelos assuntos
da obra na Open Library e editável no PUT.

A nota (`rating`) vai de 1 a 5 e o comentário (`comment`) tem até 500 caracteres. O mesmo livro
(`ol_key`) não entra duas vezes na estante: a API responde 409.

## Estrutura

```
app/
  main.py                   aplicação e registro das rotas
  db.py                     conexão com o banco (DATABASE_URL)
  security.py               CORS, headers de segurança e limite de buscas
  models/book.py            esquemas Pydantic
  models/book_orm.py        tabela books (SQLAlchemy)
  routes/health.py          GET /health
  routes/books.py           GET /books/search
  routes/shelf.py           CRUD /shelf
  services/reading.py       regras de status e resumo
  services/insights.py      perfil de leitura
  services/genres.py        tipo do livro a partir dos assuntos da Open Library
  services/open_library.py  cliente da Open Library
tests/                      testes com pytest
```

## Testes

```bash
pip install -r requirements.txt
python -m pytest -q
```

Os testes usam um banco SQLite em memória e simulam a Open Library, então rodam sem internet.

## Segurança

- CORS com lista de origens permitidas, sem refletir o `Origin` recebido.
- Headers `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`,
  `Referrer-Policy` e `Permissions-Policy` em todas as respostas.
- Limite de 60 buscas por minuto por IP em `/books/search` (429 com `Retry-After`).
- Consultas pelo ORM, com parâmetros; a ordenação aceita apenas valores de uma lista fechada.
- Falha ou demora da Open Library vira 502 com mensagem clara, sem detalhe interno.
- O container roda com usuário sem privilégios.
