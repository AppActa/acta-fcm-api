from types import SimpleNamespace
from unittest.mock import ANY, Mock

import pytest
from fastapi.testclient import TestClient

from app.database.postgres import get_conn
from app.main import app
from app.routes import dispositivo
from app.services import autenticacao


class ClientePG:
    resposta = SimpleNamespace(status_code=200, json=lambda: {'idUsuario': 123, 'idEmpresa': 42})

    def __init__(self, timeout):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, headers):
        return self.resposta


@pytest.fixture
def cliente(monkeypatch):
    app.dependency_overrides[get_conn] = lambda: object()
    monkeypatch.setattr(autenticacao, 'ACTA_PG_API_URL', 'https://acta-pg-api.teste')
    monkeypatch.setattr(autenticacao, 'AsyncClient', ClientePG)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_put_dispositivo_associa_fid_ao_usuario_da_sessao_e_nao_o_devolve(cliente, monkeypatch):
    atualizar = Mock(return_value=True)
    monkeypatch.setattr(dispositivo, 'atualizar_fid_firebase', atualizar)

    resposta = cliente.put(
        '/api/v1/me/dispositivo',
        headers={'Authorization': 'Bearer firebase-id-token'},
        json={'fidFirebase': 'fid-privado'},
    )

    assert resposta.status_code == 204
    assert resposta.content == b''
    atualizar.assert_called_once_with(ANY, 123, 'fid-privado')


def test_delete_dispositivo_remove_fid_do_usuario_da_sessao(cliente, monkeypatch):
    remover = Mock()
    monkeypatch.setattr(dispositivo, 'remover_fid_firebase', remover)

    resposta = cliente.delete('/api/v1/me/dispositivo', headers={'Authorization': 'Bearer firebase-id-token'})

    assert resposta.status_code == 204
    assert resposta.content == b''
    remover.assert_called_once_with(ANY, 123)


def test_dispositivo_exige_bearer_token(cliente):
    resposta = cliente.delete('/api/v1/me/dispositivo')

    assert resposta.status_code == 401