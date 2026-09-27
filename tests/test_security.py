"""Testes de headers de seguranca e CORS."""

FRONT = "http://localhost:8080"


def test_headers(client):
    for path in ("/health", "/shelf/999"):
        h = client.get(path).headers
        assert h["X-Content-Type-Options"] == "nosniff"
        assert h["X-Frame-Options"] == "DENY"
        assert h["Referrer-Policy"] == "no-referrer"
        assert "frame-ancestors 'none'" in h["Content-Security-Policy"]


def test_cors_front(client):
    res = client.get("/health", headers={"Origin": FRONT})
    assert res.headers["access-control-allow-origin"] == FRONT


def test_cors_unknown(client):
    res = client.get("/health", headers={"Origin": "https://site-malicioso.example"})
    assert "access-control-allow-origin" not in res.headers


def test_cors_preflight(client):
    res = client.options(
        "/shelf/1", headers={"Origin": FRONT, "Access-Control-Request-Method": "PUT"}
    )
    assert res.status_code == 200
    assert "PUT" in res.headers["access-control-allow-methods"]
