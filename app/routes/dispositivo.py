from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.database.postgres import get_conn
from app.repositories.usuarios import atualizar_fid_firebase, remover_fid_firebase
from app.schemas.schemas import FidDispositivoInput, UsuarioAutenticado
from app.services.autenticacao import obter_usuario_autenticado

router = APIRouter(prefix='/api/v1/me/dispositivo', tags=['Dispositivo'])

@router.put('', status_code=status.HTTP_204_NO_CONTENT)
def registrar_dispositivo(dados: FidDispositivoInput, conn=Depends(get_conn), usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)):
    if not atualizar_fid_firebase(conn, usuario.id_usuario, dados.fid_firebase):
        raise HTTPException(status_code=403, detail='Usuário não está ativo')

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete('', status_code=status.HTTP_204_NO_CONTENT)
def revogar_dispositivo(conn=Depends(get_conn), usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)):
    remover_fid_firebase(conn, usuario.id_usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)