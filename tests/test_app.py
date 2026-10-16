from fastapi.testclient import TestClient
from app.main import app

def test_app_inicia_e_responde_health():
    with TestClient(app) as cliente:
        resposta = cliente.get('/health')

    assert resposta.status_code == 200
    assert resposta.json() == {'status': 'ok', 'service': 'acta-fcm-api'}

def test_http_exception_usa_formato_acta():
    with TestClient(app) as cliente:
        resposta = cliente.get('/rota-inexistente')

    assert resposta.status_code == 404
    assert resposta.json()['httpStatus'] == 404
    assert resposta.json()['mensagens'] == ['Not Found']