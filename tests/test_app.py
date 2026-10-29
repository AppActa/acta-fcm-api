import asyncio
import logging
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from starlette.requests import Request
from app.main import app
from app.error_handlers import tratar_erro_inesperado
from app.routes import health
from app.schemas.health import HealthResponse


def test_app_inicia_e_responde_health(monkeypatch):
    monkeypatch.setattr(health, 'verificar_saude', lambda: HealthResponse(
        status='UP', banco='UP', auth='UP', firebase='UP', mensagem='ok',
        verificado_em=datetime.now(timezone.utc),
    ))
    with TestClient(app) as cliente:
        resposta = cliente.get('/health')

    assert resposta.status_code == 200
    assert resposta.json()['status'] == 'UP'

def test_http_exception_usa_formato_acta():
    with TestClient(app) as cliente:
        resposta = cliente.get('/rota-inexistente')

    assert resposta.status_code == 404
    assert resposta.json()['httpStatus'] == 404
    assert resposta.json()['mensagens'] == ['Not Found']


def test_docs_raiz_redireciona_para_swagger_com_openapi_carregado(monkeypatch):
    monkeypatch.setattr(health, 'verificar_saude', lambda: HealthResponse(
        status='UP', banco='UP', auth='UP', firebase='UP', mensagem='ok',
        verificado_em=datetime.now(timezone.utc),
    ))
    with TestClient(app) as cliente:
        resposta = cliente.get('/docs')

    assert resposta.status_code == 200
    assert 'swagger-ui' in resposta.text.lower()
    assert '/api/v1/me/openapi.json' in resposta.text


def test_log_de_erro_inesperado_nao_expoe_detalhe_da_excecao(caplog):
    request = Request({
        'type': 'http', 'http_version': '1.1', 'method': 'GET', 'scheme': 'http',
        'path': '/', 'raw_path': b'/', 'query_string': b'', 'headers': [],
        'server': ('test', 80), 'client': ('test', 1), 'root_path': '',
    })
    detalhe = 'fid-sintetico bearer-sintetico'

    with caplog.at_level(logging.ERROR):
        asyncio.run(tratar_erro_inesperado(request, RuntimeError(detalhe)))

    assert detalhe not in caplog.text
    assert 'RuntimeError' in caplog.text