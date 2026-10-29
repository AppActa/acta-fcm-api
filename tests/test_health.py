from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from google.auth.exceptions import RefreshError
from psycopg2 import OperationalError

from app.main import app
from app.services import fcm, health

SEGREDO_SINTETICO = 'segredo-sintetico-nao-deve-aparecer-na-resposta'


class BancoDeTeste:
    indisponivel = False

    def connect(self, *args, **kwargs):
        if self.indisponivel:
            raise OperationalError(SEGREDO_SINTETICO)
        return self

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, *args):
        pass

    def fetchone(self):
        return (1,)

    def close(self):
        pass


class CredencialDeTeste:
    valid = True
    indisponivel = False

    def refresh(self, request):
        if self.indisponivel:
            raise RefreshError(SEGREDO_SINTETICO)
        self.valid = True


@pytest.fixture
def ambiente(monkeypatch):
    banco = BancoDeTeste()
    credencial = CredencialDeTeste()
    auth = SimpleNamespace(resposta=httpx.Response(200, json={'status': 'UP'}))

    def responder_auth(request):
        assert str(request.url) == 'https://auth.test/api/v1/health'
        return auth.resposta

    cliente_http = httpx.Client
    monkeypatch.setattr(health, 'DB_URL', 'postgresql://health.test/banco-sintetico')
    monkeypatch.setattr(health, 'ACTA_AUTH_API_URL', 'https://auth.test/api/v1')
    monkeypatch.setattr(health, 'connect', banco.connect)
    monkeypatch.setattr(health, 'Client', lambda **kwargs: cliente_http(transport=httpx.MockTransport(responder_auth), **kwargs))
    monkeypatch.setattr(fcm, 'get_app', lambda: SimpleNamespace(credential=SimpleNamespace(get_credential=lambda: credencial)))

    def envio_proibido(*args, **kwargs):
        pytest.fail('Health não deve enviar notificações')

    monkeypatch.setattr(fcm, 'send', envio_proibido)
    with TestClient(app) as cliente:
        yield SimpleNamespace(cliente=cliente, banco=banco, auth=auth, firebase=credencial)


def test_health_retorna_200_com_componentes_up_mensagem_e_horario_com_fuso(ambiente):
    resposta = ambiente.cliente.get('/health')

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert {k: corpo[k] for k in ('status', 'banco', 'auth', 'firebase')} == {
        'status': 'UP', 'banco': 'UP', 'auth': 'UP', 'firebase': 'UP',
    }
    assert corpo['mensagem'] == 'O CATO verificou: API, banco de dados, Auth API e credenciais do Firebase estão funcionando!'
    instante = datetime.fromisoformat(corpo['verificadoEm'].replace('Z', '+00:00'))
    assert instante.tzinfo is not None
    assert abs((datetime.now(timezone.utc) - instante).total_seconds()) < 5


@pytest.mark.parametrize('componente', ['banco', 'auth', 'firebase'])
def test_health_retorna_503_identifica_componente_indisponivel_e_nao_expoe_segredos(ambiente, componente):
    if componente == 'banco':
        ambiente.banco.indisponivel = True
    elif componente == 'auth':
        ambiente.auth.resposta = httpx.Response(503, text=SEGREDO_SINTETICO)
    else:
        ambiente.firebase.valid = False
        ambiente.firebase.indisponivel = True

    resposta = ambiente.cliente.get('/health')

    assert resposta.status_code == 503
    corpo = resposta.json()
    assert corpo['status'] == 'DOWN'
    assert corpo[componente] == 'DOWN'
    assert all(corpo[k] == 'UP' for k in ('banco', 'auth', 'firebase') if k != componente)
    assert corpo['mensagem'] == 'O CATO verificou: Um ou mais componentes estão indisponíveis...'
    assert SEGREDO_SINTETICO not in resposta.text


def test_health_retorna_503_quando_todas_as_dependencias_estao_down(ambiente):
    ambiente.banco.indisponivel = True
    ambiente.auth.resposta = httpx.Response(503)
    ambiente.firebase.valid = False
    ambiente.firebase.indisponivel = True

    resposta = ambiente.cliente.get('/health')

    assert resposta.status_code == 503
    assert resposta.json()['status'] == 'DOWN'
    assert all(resposta.json()[componente] == 'DOWN' for componente in ('banco', 'auth', 'firebase'))


def test_swagger_documenta_200_e_503_com_o_mesmo_formato_publico(ambiente):
    resposta = ambiente.cliente.get('/api/v1/me/openapi.json')

    assert resposta.status_code == 200
    contrato = resposta.json()
    operacao = contrato['paths']['/health']['get']
    assert '/api/v1/health' not in contrato['paths']
    assert not operacao.get('security')
    assert {'200', '503'} <= operacao['responses'].keys()
    campos = {'status', 'banco', 'auth', 'firebase', 'mensagem', 'verificadoEm'}
    for status in ('200', '503'):
        schema = operacao['responses'][status]['content']['application/json']['schema']
        if '$ref' in schema:
            schema = contrato['components']['schemas'][schema['$ref'].split('/')[-1]]
        assert set(schema['required']) == campos
        for componente in ('status', 'banco', 'auth', 'firebase'):
            assert set(schema['properties'][componente]['enum']) == {'UP', 'DOWN'}
        assert schema['properties']['verificadoEm']['format'] == 'date-time'


def test_health_considera_auth_down_mesmo_quando_http_200_informa_down(ambiente):
    ambiente.auth.resposta = httpx.Response(200, json={'status': 'DOWN'})

    resposta = ambiente.cliente.get('/health')

    assert resposta.status_code == 503
    assert resposta.json()['auth'] == 'DOWN'
    assert resposta.json()['status'] == 'DOWN'


def test_health_renova_credencial_firebase_antes_de_informar_up(ambiente):
    ambiente.firebase.valid = False

    resposta = ambiente.cliente.get('/health')

    assert resposta.status_code == 200
    assert resposta.json()['firebase'] == 'UP'
    assert resposta.json()['status'] == 'UP'


def test_health_antigo_nao_e_mais_exposto(ambiente):
    assert ambiente.cliente.get('/api/v1/health').status_code == 404
