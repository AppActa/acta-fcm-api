from unittest.mock import Mock
from secrets import token_urlsafe

import pytest
import logging
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from requests.exceptions import Timeout
from app.services import fcm
from app.schemas.schemas import FalhaEnvioPush

def test_enviar_push_usa_fid_oficial_e_apenas_referencia_opaca(monkeypatch):
    enviar = Mock(return_value='mensagem-fcm-id')
    monkeypatch.setattr(fcm, 'send', enviar)
    monkeypatch.setattr(fcm, '_firebase_app', lambda: object())
    conn = object()
    fid_sintetico = token_urlsafe(32)

    resposta = fcm.enviar_push(conn, 123, fid_sintetico, 456)

    mensagem = enviar.call_args.args[0]
    assert resposta == 'mensagem-fcm-id'
    assert mensagem.notification is None
    assert mensagem.data == {'idNotificacao': '456'}
    assert mensagem.android.priority == 'high'
    assert mensagem.fid
    assert mensagem.token is None

def test_enviar_push_invalida_destino_expirado_sem_expo_lo_em_logs(monkeypatch, caplog):
    enviar = Mock(side_effect=messaging.UnregisteredError('destino inválido'))
    limpar = Mock()
    monkeypatch.setattr(fcm, 'send', enviar)
    monkeypatch.setattr(fcm, '_firebase_app', lambda: object())
    monkeypatch.setattr(fcm, 'limpar_fid_se_igual', limpar)
    conn = object()
    fid_sintetico = token_urlsafe(32)

    with caplog.at_level(logging.INFO):
        with pytest.raises(FalhaEnvioPush) as erro:
            fcm.enviar_push(conn, 123, fid_sintetico, 456)

    limpar.assert_called_once_with(conn, 123, fid_sintetico)
    assert erro.value.destino_invalido is True
    assert erro.value.recuperavel is False
    assert fid_sintetico not in caplog.text


def test_enviar_push_classifica_falha_temporaria_sem_reportar_sucesso(monkeypatch):
    monkeypatch.setattr(fcm, 'send', Mock(side_effect=FirebaseError('unavailable', 'temporariamente indisponível')))
    monkeypatch.setattr(fcm, '_firebase_app', lambda: object())

    with pytest.raises(FalhaEnvioPush) as erro:
        fcm.enviar_push(object(), 123, token_urlsafe(32), 456)

    assert erro.value.recuperavel is True
    assert erro.value.codigo == 'unavailable'


def test_enviar_push_classifica_timeout_de_transporte_como_recuperavel(monkeypatch):
    monkeypatch.setattr(fcm, 'send', Mock(side_effect=Timeout()))
    monkeypatch.setattr(fcm, '_firebase_app', lambda: object())

    with pytest.raises(FalhaEnvioPush) as erro:
        fcm.enviar_push(object(), 123, token_urlsafe(32), 456)

    assert erro.value.recuperavel is True


def test_enviar_push_nao_confirma_resposta_vazia_do_sdk(monkeypatch):
    monkeypatch.setattr(fcm, 'send', Mock(return_value=''))
    monkeypatch.setattr(fcm, '_firebase_app', lambda: object())

    with pytest.raises(FalhaEnvioPush) as erro:
        fcm.enviar_push(object(), 123, token_urlsafe(32), 456)

    assert erro.value.codigo == 'empty-firebase-response'
    assert erro.value.recuperavel is True


def test_app_firebase_exige_projeto_configurado_e_define_timeout(monkeypatch):
    app = object()
    inicializar = Mock(return_value=app)
    monkeypatch.setattr(fcm, 'get_app', Mock(side_effect=ValueError()))
    monkeypatch.setattr(fcm, 'initialize_app', inicializar)
    monkeypatch.setattr(fcm, 'FIREBASE_PROJECT_ID', 'projeto-sintetico')

    assert fcm._firebase_app() is app
    assert inicializar.call_args.kwargs['options'] == {
        'projectId': 'projeto-sintetico',
        'httpTimeout': fcm.TIMEOUT_SECONDS,
    }


def test_app_firebase_rejeita_projeto_incompativel(monkeypatch):
    monkeypatch.setattr(fcm, 'get_app', Mock(return_value=type('FirebaseApp', (), {'project_id': 'outro-projeto'})()))
    monkeypatch.setattr(fcm, 'FIREBASE_PROJECT_ID', 'projeto-esperado')

    with pytest.raises(RuntimeError):
        fcm._firebase_app()
