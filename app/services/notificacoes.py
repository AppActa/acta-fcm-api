import logging
from fastapi import HTTPException
from app.repositories import notificacoes as repository
from app.repositories import usuarios as usuario_repository
from app.schemas.catalogo import (
    CATEGORIAS_NOTIFICACAO,
    ENTIDADE_POR_CATEGORIA,
    MENSAGENS_PUSH,
    ROTAS_ENTIDADE,
    TIPOS_EVENTO,
)
from app.services.fcm import enviar_push

logger = logging.getLogger(__name__)

def _personalizar_mensagem_push(nome: str | None, texto: str) -> str:
    primeiro_nome = (nome or '').strip().split(maxsplit=1)
    if not primeiro_nome:
        return texto
    return f'Olá, {primeiro_nome[0]}! {texto}'

def _enviar_push_para_destinatario(conn, id_notificacao: int, id_usuario: int, texto_push: str,) -> None:
    try:
        nome, fid_firebase = usuario_repository.obter_dados_push(conn, id_usuario)
        
        if fid_firebase is None:
            return

        mensagem = _personalizar_mensagem_push(nome, texto_push)
        enviar_push(conn, id_usuario, fid_firebase, id_notificacao, mensagem)
    except Exception as erro:
        logger.warning('Falha best-effort no push: %s', type(erro).__name__)

def listar_notificacoes(conn, id_usuario: int, apenas_nao_lidas: bool, categoria: str | None = None) -> list:
    if categoria and categoria not in CATEGORIAS_NOTIFICACAO:
        raise HTTPException(status_code=422, detail='Categoria de notificação inválida')
    return repository.listar(conn, id_usuario, apenas_nao_lidas, categoria)

def publicar_evento(conn, evento) -> dict:
    configuracao = TIPOS_EVENTO.get(evento.tipo_evento)
    if not configuracao:
        raise HTTPException(status_code=422, detail='Tipo de evento não permitido')

    categoria, deve_enviar_push = configuracao
    texto_push = MENSAGENS_PUSH.get(evento.tipo_evento)
    if deve_enviar_push and not texto_push:
        raise HTTPException(status_code=500, detail='Mensagem de push não configurada para o evento')

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
    if deve_enviar_push:
        for id_notificacao, id_usuario in criadas:
            _enviar_push_para_destinatario(conn, id_notificacao, id_usuario, texto_push,)

    return {
        'quantidade_criada': len(criadas),
        'quantidade_duplicada': len(destinatarios) - len(criadas),
    }