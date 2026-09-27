"""Testes das rotas da estante."""


def add(client, book, **extra):
    res = client.post("/shelf", json={**book, **extra})
    assert res.status_code == 201, res.text
    return res.json()


def test_add(client, book):
    b = add(client, book)
    assert b["id"] > 0
    assert b["status"] == "want"
    assert b["title"] == "Dom Casmurro"
    assert b["started_at"] is None and b["finished_at"] is None


def test_add_utc(client, book):
    assert add(client, book)["added_at"].endswith("Z")


def test_add_duplicate(client, book):
    add(client, book)
    res = client.post("/shelf", json=book)
    assert res.status_code == 409
    assert res.json()["detail"] == "Este livro ja esta na estante."


def test_add_invalid(client, book):
    assert client.post("/shelf", json={**book, "title": ""}).status_code == 422
    assert client.post("/shelf", json={**book, "ol_key": "OL1W"}).status_code == 422


def test_add_ignores_api_fields(client, book):
    res = client.post(
        "/shelf",
        json={**book, "id": 99, "status": "read", "finished_at": "2020-01-01T00:00:00Z"},
    )
    assert res.status_code == 201
    assert res.json()["id"] != 99
    assert res.json()["status"] == "want"
    assert res.json()["finished_at"] is None


def test_add_search_hit(client, book):
    hit = {**book, "cover_url": "https://covers.openlibrary.org/b/id/8231856-M.jpg"}
    assert client.post("/shelf", json=hit).status_code == 201


def test_list_and_get(client, book):
    b = add(client, book)
    assert [x["id"] for x in client.get("/shelf").json()] == [b["id"]]
    assert client.get(f"/shelf/{b['id']}").json()["title"] == "Dom Casmurro"


def test_get_missing(client):
    res = client.get("/shelf/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Livro nao encontrado na estante."


def test_list_by_status(client, book):
    a = add(client, book)
    add(client, book, ol_key="/works/OL2W", title="Outro")
    client.put(f"/shelf/{a['id']}", json={"status": "reading"})
    res = client.get("/shelf", params={"status": "reading"}).json()
    assert [x["id"] for x in res] == [a["id"]]


def test_list_by_title(client, book):
    add(client, book, ol_key="/works/OL2W", title="memorias postumas")
    add(client, book, ol_key="/works/OL3W", title="Alienista")
    add(client, book)
    titles = [x["title"] for x in client.get("/shelf", params={"order": "title"}).json()]
    assert titles == ["Alienista", "Dom Casmurro", "memorias postumas"]


def test_list_invalid(client):
    assert client.get("/shelf", params={"order": "id; DROP TABLE livro"}).status_code == 422
    assert client.get("/shelf", params={"status": "pausado"}).status_code == 422


def test_update_partial(client, book):
    b = add(client, book)
    client.put(f"/shelf/{b['id']}", json={"comment": "Capitu!"})
    res = client.put(f"/shelf/{b['id']}", json={"rating": 5}).json()
    assert res["comment"] == "Capitu!"
    assert res["rating"] == 5
    assert res["status"] == "want"


def test_update_read(client, book):
    b = add(client, book)
    res = client.put(f"/shelf/{b['id']}", json={"status": "read"}).json()
    assert res["finished_at"] is not None


def test_update_invalid(client, book):
    b = add(client, book)
    url = f"/shelf/{b['id']}"
    assert client.put(url, json={"rating": 6}).status_code == 422
    assert client.put(url, json={"rating": 0}).status_code == 422
    assert client.put(url, json={"comment": "x" * 501}).status_code == 422
    assert client.put(url, json={"pagina_atual": 10}).status_code == 422
    assert client.put("/shelf/999", json={"rating": 3}).status_code == 404


def test_rating_average(client, book):
    a = add(client, book)
    b = add(client, book, ol_key="/works/OL2W", title="Outro")
    assert client.put(f"/shelf/{a['id']}", json={"rating": 1}).json()["rating"] == 1
    client.put(f"/shelf/{b['id']}", json={"rating": 4})
    assert client.get("/shelf/summary").json()["avg_rating"] == 2.5


def test_clear_rating_and_comment(client, book):
    b = add(client, book)
    client.put(f"/shelf/{b['id']}", json={"rating": 4, "comment": "Bom"})
    res = client.put(f"/shelf/{b['id']}", json={"rating": None, "comment": None}).json()
    assert (res["rating"], res["comment"]) == (None, None)


def test_remove(client, book):
    b = add(client, book)
    res = client.delete(f"/shelf/{b['id']}")
    assert res.status_code == 204
    assert res.content == b""
    assert client.get(f"/shelf/{b['id']}").status_code == 404
    assert client.delete(f"/shelf/{b['id']}").status_code == 404


def test_remove_then_add(client, book):
    b = add(client, book)
    client.delete(f"/shelf/{b['id']}")
    add(client, book)


def test_summary_route(client):
    res = client.get("/shelf/summary")
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert len(res.json()["by_month"]) == 6


def test_summary(client, book):
    a = add(client, book)
    b = add(client, book, ol_key="/works/OL2W", title="Outro", pages=100)
    add(client, book, ol_key="/works/OL3W", title="Terceiro")
    client.put(f"/shelf/{a['id']}", json={"status": "read", "rating": 5})
    client.put(f"/shelf/{b['id']}", json={"status": "reading", "rating": 4})

    res = client.get("/shelf/summary").json()
    assert (res["want"], res["reading"], res["read"], res["dropped"]) == (1, 1, 1, 0)
    assert res["pages_read"] == 256
    assert res["avg_rating"] == 4.5
    assert res["by_month"][-1]["books"] == 1
    assert "pages" not in res["by_month"][-1]


def test_dropped(client, book):
    b = add(client, book)
    client.put(f"/shelf/{b['id']}", json={"status": "reading"})
    res = client.put(f"/shelf/{b['id']}", json={"status": "dropped"}).json()
    assert res["status"] == "dropped"
    assert res["started_at"] is not None and res["finished_at"] is not None
    summary = client.get("/shelf/summary").json()
    assert (summary["dropped"], summary["read"]) == (1, 0)
