from unittest.mock import Mock
import logging
from firebase_admin import messaging
from app.services import fcm

def test_enviar_push_usa_fid_texto_personalizado_e_apenas_id_opaco(monkeypatch):
    enviar = Mock(return_value='mensagem-fcm-id')
    monkeypatch.setattr(fcm, 'send', enviar)
    monkeypatch.setattr(fcm, '_firebase_app', lambda: object())
    conn = object()

    fcm.enviar_push(conn, 123, 'fid-firebase-de-teste', 456, 'Olá, Ana! Uma tarefa foi atribuída a você.')

    mensagem = enviar.call_args.args[0]
    assert mensagem.notification.title == 'ACTA'
    assert mensagem.notification.body == 'Olá, Ana! Uma tarefa foi atribuída a você.'
    assert mensagem.data == {'idNotificacao': '456'}
    assert mensagem.fid == 'fid-firebase-de-teste'

def test_enviar_push_limpa_fid_nao_registrado_sem_expor_em_logs(monkeypatch, caplog):
    enviar = Mock(side_effect=messaging.UnregisteredError('token inválido'))
    limpar = Mock()
    monkeypatch.setattr(fcm, 'send', enviar)
    monkeypatch.setattr(fcm, '_firebase_app', lambda: object())
    monkeypatch.setattr(fcm, 'limpar_fid_se_igual', limpar)
    conn = object()

    fid = 'fid-firebase-invalido'
    with caplog.at_level(logging.INFO):
        fcm.enviar_push(conn, 123, fid, 456, 'Mensagem')

    limpar.assert_called_once_with(conn, 123, fid)
    assert fid not in caplog.text