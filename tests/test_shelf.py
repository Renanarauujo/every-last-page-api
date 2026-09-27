"""Testes das rotas da estante."""


def add(client, book, **extra):
    res = client.post("/estante", json={**book, **extra})
    assert res.status_code == 201, res.text
    return res.json()


def test_add(client, book):
    b = add(client, book)
    assert b["id"] > 0
    assert b["status"] == "quero_ler"
    assert b["titulo"] == "Dom Casmurro"
    assert b["iniciado_em"] is None and b["concluido_em"] is None


def test_add_utc(client, book):
    assert add(client, book)["adicionado_em"].endswith("Z")


def test_add_duplicate(client, book):
    add(client, book)
    res = client.post("/estante", json=book)
    assert res.status_code == 409
    assert res.json()["detail"] == "Este livro ja esta na estante."


def test_add_invalid(client, book):
    assert client.post("/estante", json={**book, "titulo": ""}).status_code == 422
    assert client.post("/estante", json={**book, "ol_key": "OL1W"}).status_code == 422


def test_add_ignores_api_fields(client, book):
    res = client.post(
        "/estante",
        json={**book, "id": 99, "status": "lido", "concluido_em": "2020-01-01T00:00:00Z"},
    )
    assert res.status_code == 201
    assert res.json()["id"] != 99
    assert res.json()["status"] == "quero_ler"
    assert res.json()["concluido_em"] is None


def test_add_search_hit(client, book):
    hit = {**book, "capa_url": "https://covers.openlibrary.org/b/id/8231856-M.jpg"}
    assert client.post("/estante", json=hit).status_code == 201


def test_list_and_get(client, book):
    b = add(client, book)
    assert [x["id"] for x in client.get("/estante").json()] == [b["id"]]
    assert client.get(f"/estante/{b['id']}").json()["titulo"] == "Dom Casmurro"


def test_get_missing(client):
    res = client.get("/estante/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Livro nao encontrado na estante."


def test_list_by_status(client, book):
    a = add(client, book)
    add(client, book, ol_key="/works/OL2W", titulo="Outro")
    client.put(f"/estante/{a['id']}", json={"status": "lendo"})
    res = client.get("/estante", params={"status": "lendo"}).json()
    assert [x["id"] for x in res] == [a["id"]]


def test_list_by_title(client, book):
    add(client, book, ol_key="/works/OL2W", titulo="memorias postumas")
    add(client, book, ol_key="/works/OL3W", titulo="Alienista")
    add(client, book)
    titles = [x["titulo"] for x in client.get("/estante", params={"ordem": "titulo"}).json()]
    assert titles == ["Alienista", "Dom Casmurro", "memorias postumas"]


def test_list_invalid(client):
    assert client.get("/estante", params={"ordem": "id; DROP TABLE livro"}).status_code == 422
    assert client.get("/estante", params={"status": "pausado"}).status_code == 422


def test_update_partial(client, book):
    b = add(client, book)
    client.put(f"/estante/{b['id']}", json={"comentario": "Capitu!"})
    res = client.put(f"/estante/{b['id']}", json={"nota": 5}).json()
    assert res["comentario"] == "Capitu!"
    assert res["nota"] == 5
    assert res["status"] == "quero_ler"


def test_update_read(client, book):
    b = add(client, book)
    res = client.put(f"/estante/{b['id']}", json={"status": "lido"}).json()
    assert res["concluido_em"] is not None


def test_update_invalid(client, book):
    b = add(client, book)
    url = f"/estante/{b['id']}"
    assert client.put(url, json={"nota": 6}).status_code == 422
    assert client.put(url, json={"nota": 0}).status_code == 422
    assert client.put(url, json={"comentario": "x" * 501}).status_code == 422
    assert client.put(url, json={"pagina_atual": 10}).status_code == 422
    assert client.put("/estante/999", json={"nota": 3}).status_code == 404


def test_rating_average(client, book):
    a = add(client, book)
    b = add(client, book, ol_key="/works/OL2W", titulo="Outro")
    assert client.put(f"/estante/{a['id']}", json={"nota": 1}).json()["nota"] == 1
    client.put(f"/estante/{b['id']}", json={"nota": 4})
    assert client.get("/estante/resumo").json()["nota_media"] == 2.5


def test_clear_rating_and_comment(client, book):
    b = add(client, book)
    client.put(f"/estante/{b['id']}", json={"nota": 4, "comentario": "Bom"})
    res = client.put(f"/estante/{b['id']}", json={"nota": None, "comentario": None}).json()
    assert (res["nota"], res["comentario"]) == (None, None)


def test_remove(client, book):
    b = add(client, book)
    res = client.delete(f"/estante/{b['id']}")
    assert res.status_code == 204
    assert res.content == b""
    assert client.get(f"/estante/{b['id']}").status_code == 404
    assert client.delete(f"/estante/{b['id']}").status_code == 404


def test_remove_then_add(client, book):
    b = add(client, book)
    client.delete(f"/estante/{b['id']}")
    add(client, book)


def test_summary_route(client):
    res = client.get("/estante/resumo")
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert len(res.json()["lidos_por_mes"]) == 6


def test_summary(client, book):
    a = add(client, book)
    b = add(client, book, ol_key="/works/OL2W", titulo="Outro", total_paginas=100)
    add(client, book, ol_key="/works/OL3W", titulo="Terceiro")
    client.put(f"/estante/{a['id']}", json={"status": "lido", "nota": 5})
    client.put(f"/estante/{b['id']}", json={"status": "lendo", "nota": 4})

    res = client.get("/estante/resumo").json()
    assert (res["quero_ler"], res["lendo"], res["lidos"], res["abandonados"]) == (1, 1, 1, 0)
    assert res["paginas_lidas"] == 256
    assert res["nota_media"] == 4.5
    assert res["lidos_por_mes"][-1]["livros"] == 1
    assert "paginas" not in res["lidos_por_mes"][-1]


def test_dropped(client, book):
    b = add(client, book)
    client.put(f"/estante/{b['id']}", json={"status": "lendo"})
    res = client.put(f"/estante/{b['id']}", json={"status": "abandonado"}).json()
    assert res["status"] == "abandonado"
    assert res["iniciado_em"] is not None and res["concluido_em"] is None
    summary = client.get("/estante/resumo").json()
    assert (summary["abandonados"], summary["lidos"]) == (1, 0)
