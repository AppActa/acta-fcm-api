import logging
from firebase_admin import get_app, initialize_app
from firebase_admin.messaging import Message, Notification, SenderIdMismatchError, UnregisteredError, send
from firebase_admin.exceptions import FirebaseError
from app.config import FIREBASE_PROJECT_ID
from app.repositories.usuarios import limpar_fid_se_igual

logger = logging.getLogger(__name__)

def _firebase_app():
    try:
        return get_app()
    except ValueError:
        opcoes = {'projectId': FIREBASE_PROJECT_ID}
        return initialize_app(options=opcoes)

def enviar_push(conn, id_usuario: int, fid_firebase: str, id_notificacao: int, texto: str) -> None:
    try:
        mensagem = Message(
            notification=Notification(title='ACTA', body=texto),
            data={'idNotificacao': str(id_notificacao)},
            fid=fid_firebase,
        )
        send(mensagem, app=_firebase_app())
    except (UnregisteredError, SenderIdMismatchError):
        limpar_fid_se_igual(conn, id_usuario, fid_firebase)
        logger.info('FID inválido removido para usuário %s', id_usuario)
    except FirebaseError as erro:
        logger.warning('Falha no envio FCM para usuário %s: %s', id_usuario, type(erro).__name__)
    except Exception as erro:
        logger.warning('FCM indisponível para usuário %s: %s', id_usuario, type(erro).__name__)