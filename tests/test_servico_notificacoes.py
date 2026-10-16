from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.schemas.schemas import EventoNotificacao
from app.services import notificacoes

class Cursor:
    def __init__(self, linhas=()):
        self.linhas = linhas
        self.executados = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, parametros):
        self.executados.append((sql, parametros))

    def fetchall(self):
        return self.linhas

class Connection:
    def __init__(self, linhas=()):
        self.cursor_obj = Cursor(linhas)

    def cursor(self):
        return self.cursor_obj

def evento(tipo='TAREFA_ATRIBUIDA', entidade='TAREFA', deep_link='acta://tarefas/987'):
    return EventoNotificacao.model_validate({
        'idEvento': 'evento-1',
        'tipoEvento': tipo,
        'ocorridoEm': '2026-10-14T09:30:00-03:00',
        'idEmpresa': 42,
        'idsDestinatarios': [123],
        'tipoEntidade': entidade,
        'idEntidade': '987',
        'deepLink': deep_link,
        'chaveDeduplicacao': 'tarefa-987-atribuicao-3',
    })

def test_publicar_evento_rejeita_tipo_desconhecido():
    with pytest.raises(HTTPException) as erro:
        notificacoes.publicar_evento(Connection(), evento(tipo='EVENTO_INVALIDO'))

    assert erro.value.status_code == 422

def test_publicar_evento_rejeita_deep_link_fora_da_allowlist():
    with pytest.raises(HTTPException) as erro:
        notificacoes.publicar_evento(
            Connection(),
            evento(deep_link='https://exemplo.invalid/tarefa/987'),
        )

    assert erro.value.status_code == 422

def test_publicar_evento_rejeita_destinatario_de_outra_empresa():
    conn = Connection(linhas=[])

    with pytest.raises(HTTPException) as erro:
        notificacoes.publicar_evento(conn, evento())

    assert erro.value.status_code == 422
    assert 'id = ANY' in conn.cursor_obj.executados[0][0]

def test_publicar_evento_persiste_e_envia_push_com_primeiro_nome(monkeypatch):
    conn = Connection(linhas=[(123,)])
    inserir = Mock(return_value=[(456, 123)])
    buscar_dados_push = Mock(return_value=('Ana Souza', 'token-secreto'))
    enviar = Mock()
    monkeypatch.setattr(notificacoes.repository, 'inserir_evento', inserir)
    monkeypatch.setattr(notificacoes.usuario_repository, 'obter_dados_push', buscar_dados_push)
    monkeypatch.setattr(notificacoes, 'enviar_push', enviar)

    resposta = notificacoes.publicar_evento(conn, evento())

    assert resposta == {'quantidade_criada': 1, 'quantidade_duplicada': 0}
    inserir.assert_called_once()
    enviar.assert_called_once_with(
        conn,
        123,
        'token-secreto',
        456,
        'Olá, Ana! Uma tarefa foi atribuída a você.',
    )

def test_publicar_evento_de_central_nao_tenta_push(monkeypatch):
    conn = Connection(linhas=[(123,)])
    monkeypatch.setattr(notificacoes.repository, 'inserir_evento', Mock(return_value=[(456, 123)]))
    enviar = Mock()
    monkeypatch.setattr(notificacoes, 'enviar_push', enviar)

    resposta = notificacoes.publicar_evento(
        conn,
        evento(tipo='TAREFA_BLOQUEADA'),
    )

    assert resposta['quantidade_criada'] == 1
    enviar.assert_not_called()

def test_publicar_evento_duplicado_nao_reenvia_push(monkeypatch):
    conn = Connection(linhas=[(123,)])
    monkeypatch.setattr(notificacoes.repository, 'inserir_evento', Mock(return_value=[]))
    enviar = Mock()
    monkeypatch.setattr(notificacoes, 'enviar_push', enviar)

    resposta = notificacoes.publicar_evento(conn, evento())

    assert resposta == {'quantidade_criada': 0, 'quantidade_duplicada': 1}
    enviar.assert_not_called()

def test_listar_notificacoes_rejeita_categoria_invalida():
    with pytest.raises(HTTPException) as erro:
        notificacoes.listar_notificacoes(Connection(), 123, False, 'DESCONHECIDA')

    assert erro.value.status_code == 422