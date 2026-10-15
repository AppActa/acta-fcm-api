from fastapi import APIRouter, Depends, status
from app.database.postgres import get_conn
from app.schemas.schemas import EventoNotificacao, EventoNotificacaoResponse
from app.services.autenticacao import validar_produtor_interno
from app.services.notificacoes import publicar_evento

router = APIRouter(prefix='/internal/v1/eventos', tags=['Eventos internos'])

@router.post('', response_model=EventoNotificacaoResponse, status_code=status.HTTP_200_OK)
def receber_evento(evento: EventoNotificacao, conn=Depends(get_conn), _: None = Depends(validar_produtor_interno)):
    return publicar_evento(conn, evento)