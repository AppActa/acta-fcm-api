import logging
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from app.schemas.schemas import ErroResponse

logger = logging.getLogger(__name__)

def _resposta_erro(mensagens: list[str], http_status: int, headers: dict | None = None) -> JSONResponse:
    erro = ErroResponse(mensagens=mensagens, http_status=http_status,)

    return JSONResponse(
        status_code=http_status,
        content=erro.model_dump(mode='json', by_alias=True),
        headers=headers,
    )

async def tratar_http_exception(_: Request, erro: StarletteHTTPException) -> JSONResponse:
    detalhe = erro.detail
    mensagens = [str(m) for m in detalhe] if isinstance(detalhe, list) else [str(detalhe)]
    return _resposta_erro(mensagens, erro.status_code, erro.headers)

async def tratar_validacao(_: Request, erro: RequestValidationError) -> JSONResponse:
    mensagens = []
    for detalhe in erro.errors():
        local = [str(parte) for parte in detalhe.get('loc', ()) if parte not in ('body', 'query', 'path')]
        mensagem = detalhe.get('msg', 'Valor inválido')
        mensagens.append(f"{'/'.join(local)}: {mensagem}" if local else mensagem)
    return _resposta_erro(mensagens, 400)

async def tratar_erro_inesperado(_: Request, erro: Exception) -> JSONResponse:
    logger.error('Erro interno não tratado na acta-fcm-api', exc_info=(type(erro), erro, erro.__traceback__),)
    return _resposta_erro(['Ocorreu um erro interno inesperado'], 500)