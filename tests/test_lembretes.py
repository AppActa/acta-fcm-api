from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from app.services import lembretes
from app.jobs import lembretes as job

@pytest.fixture
def cenario(monkeypatch):
    instante = datetime(2026, 10, 15, 9, tzinfo=lembretes.FUSO)
    candidato = dict(id=10, id_responsavel=123, id_empresa=42,
                     data_fim_prevista=instante.date() + timedelta(days=1))
    listar = Mock(side_effect=[[candidato], []])
    obter = Mock(return_value=candidato)
    publicar = Mock(return_value=dict(quantidade_criada=1, quantidade_duplicada=0))
    monkeypatch.setattr(lembretes, '_agora', lambda: instante)
    monkeypatch.setattr(lembretes.repository, 'listar_candidatos', listar)
    monkeypatch.setattr(lembretes.repository, 'obter_candidato', obter)
    monkeypatch.setattr(lembretes, 'publicar_evento', publicar)
    return Mock(), candidato, listar, obter, publicar

def test_vespera_usa_prazo_local_e_evento_com_destinatario_atual(cenario):
    conn, candidato, listar, obter, publicar = cenario
    obter.return_value = {**candidato, 'id_responsavel': 124}

    totais = lembretes.executar_lembretes(conn)

    evento = publicar.call_args.args[1]
    assert evento.tipo_evento == 'TAREFA_VENCE_AMANHA'
    assert evento.ids_destinatarios == [124]
    assert evento.id_empresa == 42
    assert evento.deep_link == 'acta://tarefas/10'
    assert evento.chave_deduplicacao == 'tarefa-vence-amanha:10:2026-10-16'
    assert evento.ocorrido_em.utcoffset() == timedelta(hours=-3)
    assert totais['criadas'] == 1
    assert listar.call_args.args[2] == 10

def test_tarefa_que_deixou_de_ser_elegivel_e_ignorada(cenario):
    conn, _, _, obter, publicar = cenario
    obter.return_value = None
    totais = lembretes.executar_lembretes(conn)
    assert totais['ignoradas'] == 1
    publicar.assert_not_called()

def test_falha_de_um_item_recupera_conexao_e_continua(cenario):
    conn, candidato, listar, obter, publicar = cenario
    outro = {**candidato, 'id': 11}
    listar.side_effect = [[candidato, outro], []]
    obter.side_effect = [RuntimeError('erro com dado restrito'), outro]

    totais = lembretes.executar_lembretes(conn)

    assert totais['falhas'] == 1
    assert totais['criadas'] == 1
    assert conn.rollback.call_count == 2
    assert publicar.call_args.args[1].id_entidade == '11'

def test_reexecucao_contabiliza_duplicata(cenario):
    conn, _, _, _, publicar = cenario
    publicar.return_value = dict(quantidade_criada=0, quantidade_duplicada=1)
    totais = lembretes.executar_lembretes(conn)
    assert totais['duplicadas'] == 1
    assert totais['criadas'] == 0

def test_interrompe_ao_virar_dia_sem_enviar_aviso_desatualizado(cenario, monkeypatch):
    conn, _, _, _, publicar = cenario
    momentos = iter([
        datetime(2026, 10, 15, 23, 59, tzinfo=lembretes.FUSO),
        datetime(2026, 10, 16, 0, 0, tzinfo=lembretes.FUSO),
    ])
    monkeypatch.setattr(lembretes, '_agora', lambda: next(momentos))
    lembretes.executar_lembretes(conn)
    publicar.assert_not_called()

def test_data_e_local_mesmo_quando_utc_ja_esta_no_dia_seguinte(cenario, monkeypatch):
    conn, _, listar, _, _ = cenario
    instante = datetime(2026, 10, 15, 23, 30, tzinfo=lembretes.FUSO)
    monkeypatch.setattr(lembretes, '_agora', lambda: instante)
    lembretes.executar_lembretes(conn)
    assert listar.call_args_list[0].args[1].isoformat() == '2026-10-16'

@pytest.mark.parametrize('falhas,esperado', [(0, 0), (1, 1)])
def test_job_retorna_status_para_agendador(monkeypatch, falhas, esperado):
    monkeypatch.setattr('sys.argv', ['lembretes'])
    conn = Mock()
    def conexao():
        yield conn
    executar = Mock(return_value={'falhas': falhas})
    monkeypatch.setattr(job, 'get_conn', conexao)
    monkeypatch.setattr(job, 'executar_lembretes', executar)
    assert job.main() == esperado
    executar.assert_called_once_with(conn)

def test_job_falha_sem_imprimir_segredo(monkeypatch, caplog):
    monkeypatch.setattr('sys.argv', ['lembretes'])
    def conexao():
        raise RuntimeError('senha-restrita')
        yield
    monkeypatch.setattr(job, 'get_conn', conexao)
    assert job.main() == 1
    assert 'senha-restrita' not in caplog.text
