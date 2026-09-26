from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_saude_responde_ok():
    resposta = client.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
