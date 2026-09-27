"""Testes das rotas de saude e raiz."""


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"name": "Every Last Page API", "docs": "/docs"}
