import pytest
from pydantic import ValidationError
from app.schemas.catalogo import MENSAGENS_PUSH, TIPOS_EVENTO
from app.schemas.schemas import EventoNotificacao, FidDispositivoInput

def evento_json(**alteracoes):
    dados = {
        'idEvento': 'evento-1',
        'tipoEvento': 'TAREFA_ATRIBUIDA',
        'ocorridoEm': '2026-10-14T09:30:00-03:00',
        'idEmpresa': 42,
        'idsDestinatarios': [123],
        'tipoEntidade': 'TAREFA',
        'idEntidade': '987',
        'deepLink': 'acta://tarefas/987',
        'chaveDeduplicacao': 'tarefa-987-atribuicao-3',
    }
    return {**dados, **alteracoes}

def test_evento_notificacao_aceita_aliases_camel_case():
    evento = EventoNotificacao.model_validate(evento_json())

    assert evento.tipo_evento == 'TAREFA_ATRIBUIDA'
    assert evento.ids_destinatarios == [123]
    assert evento.ocorrido_em.utcoffset().total_seconds() == -3 * 60 * 60

def test_evento_notificacao_rejeita_data_sem_fuso_horario():
    with pytest.raises(ValidationError):
        EventoNotificacao.model_validate(evento_json(ocorridoEm='2026-10-14T09:30:00'))

def test_evento_notificacao_rejeita_destinatario_nao_positivo():
    with pytest.raises(ValidationError):
        EventoNotificacao.model_validate(evento_json(idsDestinatarios=[0]))

def test_catalogo_tem_mensagem_para_todos_os_tipos_com_push():
    tipos_com_push = {tipo for tipo, (_, push) in TIPOS_EVENTO.items() if push}

    assert set(MENSAGENS_PUSH) == tipos_com_push

def test_fid_dispositivo_usa_alias_camel_case():
    dispositivo = FidDispositivoInput.model_validate({'fidFirebase': 'fid-de-teste'})
    assert dispositivo.fid_firebase == 'fid-de-teste'

@pytest.mark.parametrize('campo', ['idUsuario', 'idEmpresa'])
def test_fid_dispositivo_rejeita_identidade_enviada_pelo_app(campo):
    with pytest.raises(ValidationError):
        FidDispositivoInput.model_validate({'fidFirebase': 'fid-de-teste', campo: 999})