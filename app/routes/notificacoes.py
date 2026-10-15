from fastapi import APIRouter, Depends, HTTPException, Query
from app.database.postgres import get_conn
from app.repositories import notificacoes as repository
from app.schemas.schemas import NotificacaoResponse, UsuarioAutenticado
from app.services.autenticacao import obter_usuario_autenticado
from app.services.notificacoes import listar_notificacoes as buscar_notificacoes

router = APIRouter(prefix='/api/v1/me/notificacoes', tags=['Notificações'])

@router.get('', response_model=list[NotificacaoResponse])
def listar_notificacoes(
    apenas_nao_lidas: bool = Query(default=False, alias='apenasNaoLidas'),
    categoria: str | None = Query(default=None, min_length=1, max_length=40),
    conn=Depends(get_conn),
    usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado),
):
    return buscar_notificacoes(conn, usuario.id_usuario, apenas_nao_lidas, categoria)

@router.get('/nao-lidas/quantidade')
def quantidade_nao_lidas(conn=Depends(get_conn), usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)) -> int:
    return repository.contar_nao_lidas(conn, usuario.id_usuario)

@router.patch('/{id_notificacao}/lida', response_model=NotificacaoResponse)
def marcar_notificacao_lida(
    id_notificacao: int,
    conn=Depends(get_conn),
    usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado),
):
    notificacao = repository.marcar_lida(conn, usuario.id_usuario, id_notificacao)
    if not notificacao:
        raise HTTPException(status_code=404, detail='Notificação não encontrada')
    return notificacao

@router.post('/lidas', response_model=int)
def marcar_todas_lidas(conn=Depends(get_conn), usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)) -> int:
    return repository.marcar_todas_lidas(conn, usuario.id_usuario)