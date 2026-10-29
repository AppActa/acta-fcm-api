import secrets
from httpx import AsyncClient, RequestError
from fastapi import HTTPException, Security
from fastapi import Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import ACTA_AUTH_API_URL, INTERNAL_API_TOKEN
from app.schemas.schemas import UsuarioAutenticado

bearer = HTTPBearer(auto_error=False)

def validar_produtor_interno(x_internal_token: str | None = Header(default=None)) -> None:
    if not INTERNAL_API_TOKEN:
        raise HTTPException(status_code=503, detail='Autenticação interna não configurada')
    if not x_internal_token or not secrets.compare_digest(x_internal_token, INTERNAL_API_TOKEN):
        raise HTTPException(status_code=401, detail='Produtor não autorizado')

async def obter_usuario_autenticado(credenciais: HTTPAuthorizationCredentials | None = Security(bearer),) -> UsuarioAutenticado:
    if credenciais is None:
        raise HTTPException(status_code=401, detail='Bearer token obrigatório')

    headers = {'Authorization': f'Bearer {credenciais.credentials}'}
    try:
        async with AsyncClient(timeout=15) as cliente:
            resposta = await cliente.get(f'{ACTA_AUTH_API_URL.rstrip("/")}/me', headers=headers)
    except RequestError as erro:
        raise HTTPException(status_code=503, detail='Não foi possível consultar acta-auth-api') from erro

    if resposta.status_code in (401, 403):
        mensagem = _mensagens_da_acta_auth(resposta.status_code, resposta)
        raise HTTPException(status_code=resposta.status_code, detail=mensagem)
    if not 200 <= resposta.status_code < 300:
        raise HTTPException(status_code=502, detail='Falha ao consultar usuário autenticado')

    try:
        usuario = UsuarioAutenticado.model_validate(resposta.json())
    except (ValueError, TypeError):
        raise HTTPException(status_code=502, detail='Resposta inválida de acta-auth-api')

    return usuario

def _mensagens_da_acta_auth(status_code: int, resposta) -> list[str]:
    try:
        corpo = resposta.json()
    except ValueError:
        corpo = None

    if isinstance(corpo, dict):
        mensagens = corpo.get('mensagens')
        if isinstance(mensagens, list) and mensagens:
            return [str(mensagem) for mensagem in mensagens]

    if status_code == 401:
        return ['O ID Token do Firebase não existe ou está inválido']
    return ['Usuário não autorizado']