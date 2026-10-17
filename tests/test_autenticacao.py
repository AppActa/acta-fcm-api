import asyncio
from types import SimpleNamespace
from httpx import Response
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.services import autenticacao

class ClienteHTTP:
    resposta = None
    chamadas = []

    def __init__(self, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, headers):
        self.chamadas.append((url, headers))
        return self.resposta

def credenciais():
    return HTTPAuthorizationCredentials(scheme='Bearer', credentials='token-de-teste')

def test_obter_usuario_autenticado_converte_401_do_pg_api(monkeypatch):
    ClienteHTTP.resposta = Response(401, text='Unauthorized')
    monkeypatch.setattr(autenticacao, 'ACTA_PG_API_URL', 'https://acta-pg-api.teste')
    monkeypatch.setattr(autenticacao, 'AsyncClient', ClienteHTTP)

    with pytest.raises(HTTPException) as erro:
        asyncio.run(autenticacao.obter_usuario_autenticado(credenciais()))

    assert erro.value.status_code == 401

def test_obter_usuario_autenticado_aceita_resposta_valida_do_pg_api(monkeypatch):
    ClienteHTTP.chamadas = []
    ClienteHTTP.resposta = SimpleNamespace(
        status_code=200,
        is_error=False,
        json=lambda: {'idUsuario': 123, 'idEmpresa': 42},
    )
    monkeypatch.setattr(autenticacao, 'ACTA_PG_API_URL', 'https://acta-pg-api.teste')
    monkeypatch.setattr(autenticacao, 'AsyncClient', ClienteHTTP)

    usuario = asyncio.run(autenticacao.obter_usuario_autenticado(credenciais()))

    assert usuario.id_usuario == 123
    assert usuario.id_empresa == 42
    assert ClienteHTTP.chamadas == [(
        'https://acta-pg-api.teste/me',
        {'Authorization': 'Bearer token-de-teste'},
    )]

def test_obter_usuario_autenticado_rejeita_redirecionamento(monkeypatch):
    ClienteHTTP.resposta = SimpleNamespace(
        status_code=302,
        is_error=False,
        json=lambda: {'idUsuario': 123, 'idEmpresa': 42},
    )
    monkeypatch.setattr(autenticacao, 'ACTA_PG_API_URL', 'https://acta-pg-api.teste')
    monkeypatch.setattr(autenticacao, 'AsyncClient', ClienteHTTP)

    with pytest.raises(HTTPException) as erro:
        asyncio.run(autenticacao.obter_usuario_autenticado(credenciais()))

    assert erro.value.status_code == 502