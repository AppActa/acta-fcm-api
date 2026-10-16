import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.repositories import lembretes as repository
from app.schemas.schemas import EventoNotificacao
from app.services.notificacoes import publicar_evento

logger = logging.getLogger(__name__)
FUSO = ZoneInfo('America/Sao_Paulo')

def _agora() -> datetime:
    return datetime.now(FUSO)

def executar_lembretes(conn) -> dict[str, int]:
    data_execucao = _agora().date()
    data_prazo = data_execucao + timedelta(days=1)
    totais = dict(candidatos=0, criadas=0, duplicadas=0, ignoradas=0, falhas=0)
    apos_id = 0

    while True:
        candidatos = repository.listar_candidatos(conn, data_prazo, apos_id)
        if not candidatos:
            return totais

        for candidato in candidatos:
            apos_id = candidato['id']
            instante = _agora()

            # não enviar notificação de vence amanhã com data de uma execução anterior
            if instante.date() != data_execucao:
                return totais

            totais['candidatos'] += 1
            try:
                atual = repository.obter_candidato(conn, data_prazo, apos_id)
                if atual is None:
                    totais['ignoradas'] += 1
                    continue
                chave = f'tarefa-vence-amanha:{atual["id"]}:{data_prazo.isoformat()}'
                evento = EventoNotificacao(
                    id_evento=chave,
                    tipo_evento='TAREFA_VENCE_AMANHA',
                    ocorrido_em=instante,
                    id_empresa=atual['id_empresa'],
                    ids_destinatarios=[atual['id_responsavel']],
                    tipo_entidade='TAREFA',
                    id_entidade=str(atual['id']),
                    deep_link=f'acta://tarefas/{atual["id"]}',
                    chave_deduplicacao=chave,
                )
                resposta = publicar_evento(conn, evento)
                totais['criadas'] += resposta['quantidade_criada']
                totais['duplicadas'] += resposta['quantidade_duplicada']
            except Exception as erro:
                totais['falhas'] += 1
                logger.warning('Falha ao processar lembrete: %s', type(erro).__name__)
            finally:
                conn.rollback()
