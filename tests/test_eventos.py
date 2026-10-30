from secrets import token_urlsafe
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.database.postgres import get_conn
from app.main import app
from app.routes import eventos as rota_eventos
from app.routes import notificacoes as rota_central
from app.services import notificacoes as servico_notificacoes
from app.services import autenticacao
from app.schemas.schemas import UsuarioAutenticado
from app.services.autenticacao import obter_usuario_autenticado
from app.schemas.schemas import FalhaEnvioPush


@pytest.fixture
def cliente():
    app.dependency_overrides[get_conn] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def evento():
    return {
        'idEvento': 'atribuicao-tarefa-71',
        'tipoEvento': 'TAREFA_ATRIBUIDA',
        'ocorridoEm': '2026-10-30T10:44:47Z',
        'idEmpresa': 1,
        'idsDestinatarios': [42],
        'tipoEntidade': 'TAREFA',
        'idEntidade': '71',
        'deepLink': 'acta://tarefas/71',
        'chaveDeduplicacao': 'tarefa-atribuida-71-42',
    }


@pytest.fixture
def token_interno(monkeypatch):
    valor = token_urlsafe(32)
    monkeypatch.setattr(autenticacao, 'INTERNAL_API_TOKEN', valor)
    return valor


def test_rota_interna_existe_e_exige_autenticacao(cliente, token_interno, evento):
    resposta = cliente.post('/internal/v1/eventos', json=evento)

    assert resposta.status_code == 401
    assert resposta.json()['httpStatus'] == 401


def test_rota_interna_rejeita_token_invalido(cliente, token_interno, evento):
    resposta = cliente.post(
        '/internal/v1/eventos',
        json=evento,
        headers={'X-Internal-Token': token_urlsafe(32)},
    )

    assert resposta.status_code == 401


def test_rota_interna_retorna_503_sem_configuracao_de_autenticacao(cliente, evento, monkeypatch):
    monkeypatch.setattr(autenticacao, 'INTERNAL_API_TOKEN', None)

    resposta = cliente.post('/internal/v1/eventos', json=evento)

    assert resposta.status_code == 503


def test_rota_interna_publica_evento_com_destinatario_validado(cliente, token_interno, evento, monkeypatch):
    conexao = object()
    app.dependency_overrides[get_conn] = lambda: conexao
    publicar = Mock(return_value={'quantidade_criada': 1, 'quantidade_duplicada': 0})
    monkeypatch.setattr(rota_eventos, 'publicar_evento', publicar)

    resposta = cliente.post(
        '/internal/v1/eventos', json=evento,
        headers={'X-Internal-Token': token_interno},
    )

    assert resposta.status_code == 200
    assert resposta.json() == {'quantidadeCriada': 1, 'quantidadeDuplicada': 0}
    publicar.assert_called_once()
    assert publicar.call_args.args[0] is conexao
    assert publicar.call_args.args[1].ids_destinatarios == [42]


def test_rota_valida_destinatario_persiste_antes_de_enviar_por_fid(cliente, token_interno, evento, monkeypatch):
    from app.repositories import notificacoes as repositorio
    from app.repositories import usuarios

    etapas = []
    conexao = object()
    fid_sintetico = token_urlsafe(32)
    app.dependency_overrides[get_conn] = lambda: conexao
    monkeypatch.setattr(usuarios, 'listar_ids_ativos_da_empresa', lambda _conn, ids, empresa: set(ids))

    def inserir(_conn, _evento, _tipo, _categoria, destinatarios):
        etapas.append('persistida')
        return [(501, destinatarios[0])]

    def enviar(_conn, id_usuario, fid, id_notificacao):
        assert etapas == ['persistida']
        assert id_usuario == 42
        assert fid
        assert id_notificacao == 501

    monkeypatch.setattr(repositorio, 'inserir_evento', inserir)
    monkeypatch.setattr(usuarios, 'obter_dados_push', lambda _conn, _usuario: (None, fid_sintetico))
    enviar_push = Mock(side_effect=enviar)
    monkeypatch.setattr(servico_notificacoes, 'enviar_push', enviar_push)

    resposta = cliente.post(
        '/internal/v1/eventos', json=evento,
        headers={'X-Internal-Token': token_interno},
    )

    assert resposta.status_code == 200
    assert resposta.json()['quantidadeCriada'] == 1
    enviar_push.assert_called_once()


def test_rota_rejeita_destinatario_inativo_ou_de_outra_empresa(cliente, token_interno, evento, monkeypatch):
    from app.repositories import notificacoes as repositorio
    from app.repositories import usuarios

    app.dependency_overrides[get_conn] = lambda: object()
    persistir = Mock()
    enviar = Mock()
    monkeypatch.setattr(usuarios, 'listar_ids_ativos_da_empresa', lambda *_: set())
    monkeypatch.setattr(repositorio, 'inserir_evento', persistir)
    monkeypatch.setattr(servico_notificacoes, 'enviar_push', enviar)

    resposta = cliente.post(
        '/internal/v1/eventos', json=evento,
        headers={'X-Internal-Token': token_interno},
    )

    assert resposta.status_code == 422
    assert resposta.json()['httpStatus'] == 422
    persistir.assert_not_called()
    enviar.assert_not_called()


def test_falha_no_push_nao_impede_consulta_autenticada_da_central(cliente, token_interno, evento, monkeypatch):
    from datetime import datetime, timezone
    from app.repositories import notificacoes as repositorio_notificacoes
    from app.repositories import usuarios

    conexao = object()
    fid_sintetico = token_urlsafe(32)
    registro = {
        'id': 501,
        'tipo': 'TAREFA_ATRIBUIDA',
        'categoria': 'TAREFA',
        'tipo_entidade': 'TAREFA',
        'id_entidade': '71',
        'deep_link': 'acta://tarefas/71',
        'criado_em': datetime.now(timezone.utc),
        'lido_em': None,
        'expira_em': None,
    }
    app.dependency_overrides[get_conn] = lambda: conexao
    app.dependency_overrides[obter_usuario_autenticado] = lambda: UsuarioAutenticado(idUsuario=42, idEmpresa=1)
    monkeypatch.setattr(usuarios, 'listar_ids_ativos_da_empresa', lambda _conn, ids, _empresa: set(ids))
    monkeypatch.setattr(repositorio_notificacoes, 'inserir_evento', lambda *_: [(501, 42)])
    monkeypatch.setattr(usuarios, 'obter_dados_push', lambda *_: (None, fid_sintetico))
    monkeypatch.setattr(
        servico_notificacoes,
        'enviar_push',
        Mock(side_effect=FalhaEnvioPush('unavailable', recuperavel=True)),
    )
    listar = Mock(return_value=[registro])
    monkeypatch.setattr(rota_central.repository, 'listar', listar)

    resposta_evento = cliente.post(
        '/internal/v1/eventos', json=evento,
        headers={'X-Internal-Token': token_interno},
    )
    resposta_central = cliente.get('/api/v1/me/notificacoes')

    assert resposta_evento.status_code == 200
    assert resposta_central.status_code == 200
    assert resposta_central.json()[0]['id'] == 501
    listar.assert_called_once_with(conexao, 42, False, None)


@pytest.mark.parametrize('alteracao', [
    {'tipoEvento': 'EVENTO_DESCONHECIDO'},
    {'tipoEntidade': 'CICLO'},
    {'idEntidade': ''},
    {'deepLink': 'https://example.invalid/task/71'},
    {'chaveDeduplicacao': ''},
    {'idEmpresa': 0},
    {'idsDestinatarios': []},
    {'ocorridoEm': '2026-10-30T10:44:47'},
    {'campoExtra': 'não permitido'},
])
def test_rota_interna_valida_contrato_do_evento(cliente, token_interno, evento, alteracao):
    evento.update(alteracao)

    resposta = cliente.post(
        '/internal/v1/eventos', json=evento,
        headers={'X-Internal-Token': token_interno},
    )

    assert resposta.status_code in (400, 422)


def test_rota_interna_nao_existe_no_prefixo_publico(cliente, evento):
    resposta = cliente.post('/api/v1/me/internal/v1/eventos', json=evento)

    assert resposta.status_code == 404


def test_validacao_de_destinatario_ativo_da_empresa_antecede_persistencia(monkeypatch, evento):
    from app.schemas.schemas import EventoNotificacao

    conn = object()
    validar = Mock(return_value=set())
    persistir = Mock()
    enviar = Mock()
    monkeypatch.setattr(servico_notificacoes.usuario_repository, 'listar_ids_ativos_da_empresa', validar)
    monkeypatch.setattr(servico_notificacoes.repository, 'inserir_evento', persistir)
    monkeypatch.setattr(servico_notificacoes, 'enviar_push', enviar)

    with pytest.raises(HTTPException) as erro:
        servico_notificacoes.publicar_evento(conn, EventoNotificacao.model_validate(evento))

    assert erro.value.status_code == 422
    validar.assert_called_once_with(conn, [42], 1)
    persistir.assert_not_called()
    enviar.assert_not_called()


def test_repeticao_deduplicada_nao_tenta_enviar_novamente(monkeypatch, evento):
    from app.schemas.schemas import EventoNotificacao

    conn = object()
    monkeypatch.setattr(servico_notificacoes.usuario_repository, 'listar_ids_ativos_da_empresa', lambda *_: {42})
    inserir = Mock(return_value=[])
    enviar = Mock()
    monkeypatch.setattr(servico_notificacoes.repository, 'inserir_evento', inserir)
    monkeypatch.setattr(servico_notificacoes, 'enviar_push', enviar)

    resposta = servico_notificacoes.publicar_evento(conn, EventoNotificacao.model_validate(evento))

    assert resposta == {'quantidade_criada': 0, 'quantidade_duplicada': 1}
    inserir.assert_called_once()
    enviar.assert_not_called()
