import logging
from fastapi import HTTPException
from app.repositories import notificacoes as repository
from app.repositories import usuarios as usuario_repository
from app.schemas.catalogo import (
    CATEGORIAS_NOTIFICACAO,
    ENTIDADE_POR_CATEGORIA,
    MENSAGENS_PUSH,
    ROTAS_ENTIDADE,
    TITULOS_PUSH,
    TIPOS_EVENTO,
)
from app.schemas.schemas import FalhaEnvioPush
from app.services.fcm import enviar_push

logger = logging.getLogger(__name__)

def _enviar_push_para_destinatario(conn, id_notificacao: int, id_usuario: int, evento) -> None:
    try:
        _, fid_firebase = usuario_repository.obter_dados_push(conn, id_usuario)
        if fid_firebase is None:
            logger.info(
                'push não tentado: destino ausente tipoEvento=%s tipoEntidade=%s idEntidade=%s chaveDeduplicacao=%s',
                evento.tipo_evento, evento.tipo_entidade, evento.id_entidade, evento.chave_deduplicacao,
            )
            return
        logger.info(
            'push tentado tipoEvento=%s tipoEntidade=%s idEntidade=%s chaveDeduplicacao=%s',
            evento.tipo_evento, evento.tipo_entidade, evento.id_entidade, evento.chave_deduplicacao,
        )
        enviar_push(conn, id_usuario, fid_firebase, id_notificacao, TITULOS_PUSH[evento.tipo_evento], MENSAGENS_PUSH[evento.tipo_evento],)
        logger.info(
            'Firebase aceitou push tipoEvento=%s tipoEntidade=%s idEntidade=%s chaveDeduplicacao=%s',
            evento.tipo_evento, evento.tipo_entidade, evento.id_entidade, evento.chave_deduplicacao,
        )
    except FalhaEnvioPush as erro:
        logger.warning(
            'Firebase rejeitou push recuperavel=%s destinoInvalido=%s codigo=%s tipoEvento=%s tipoEntidade=%s idEntidade=%s chaveDeduplicacao=%s',
            erro.recuperavel, erro.destino_invalido, erro.codigo, evento.tipo_evento, evento.tipo_entidade,
            evento.id_entidade, evento.chave_deduplicacao,
        )
    except Exception as erro:
        logger.warning(
            'erro no push recuperavel=desconhecido tipoErro=%s tipoEvento=%s tipoEntidade=%s idEntidade=%s chaveDeduplicacao=%s',
            type(erro).__name__, evento.tipo_evento, evento.tipo_entidade,
            evento.id_entidade, evento.chave_deduplicacao,
        )

def listar_notificacoes(conn, id_usuario: int, apenas_nao_lidas: bool, categoria: str | None = None) -> list:
    if categoria and categoria not in CATEGORIAS_NOTIFICACAO:
        raise HTTPException(status_code=422, detail='Categoria de notificação inválida')
    return repository.listar(conn, id_usuario, apenas_nao_lidas, categoria)

def publicar_evento(conn, evento) -> dict:
    configuracao = TIPOS_EVENTO.get(evento.tipo_evento)
    if not configuracao:
        raise HTTPException(status_code=422, detail='Tipo de evento não permitido')

    categoria, deve_enviar_push = configuracao
    rota = ROTAS_ENTIDADE.get(evento.tipo_entidade)

    if (not rota or evento.tipo_entidade != ENTIDADE_POR_CATEGORIA[categoria]):
        raise HTTPException(status_code=422, detail='Entidade ou identificador inválido')

    deep_link_esperado = f'acta://{rota}/{evento.id_entidade}'
    if evento.deep_link != deep_link_esperado:
        raise HTTPException(status_code=422, detail='Deep link não permitido para a entidade')

    destinatarios = sorted(set(evento.ids_destinatarios))
    encontrados = usuario_repository.listar_ids_ativos_da_empresa(conn, destinatarios, evento.id_empresa)

    if encontrados != set(destinatarios):
        raise HTTPException(status_code=422, detail='Destinatário não pertence à empresa ou não está ativo')

    criadas = repository.inserir_evento(conn, evento, evento.tipo_evento, categoria, destinatarios)
    logger.info(
        'evento aceito tipoEvento=%s tipoEntidade=%s idEntidade=%s chaveDeduplicacao=%s',
        evento.tipo_evento, evento.tipo_entidade, evento.id_entidade, evento.chave_deduplicacao,
    )
    logger.info(
        'central persistida quantidade=%s duplicadas=%s tipoEvento=%s tipoEntidade=%s idEntidade=%s chaveDeduplicacao=%s',
        len(criadas), len(destinatarios) - len(criadas), evento.tipo_evento,
        evento.tipo_entidade, evento.id_entidade, evento.chave_deduplicacao,
    )
    if deve_enviar_push:
        for id_notificacao, id_usuario in criadas:
            _enviar_push_para_destinatario(conn, id_notificacao, id_usuario, evento)

    return {
        'quantidade_criada': len(criadas),
        'quantidade_duplicada': len(destinatarios) - len(criadas),
    }