from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import Timeout as RequestTimeout
from firebase_admin import get_app, initialize_app
from firebase_admin.messaging import AndroidConfig, Message, SenderIdMismatchError, UnregisteredError, send
from firebase_admin.exceptions import FirebaseError
from app.config import FIREBASE_PROJECT_ID
from app.repositories.usuarios import limpar_fid_se_igual
from app.schemas.schemas import FalhaEnvioPush

TIMEOUT_SECONDS = 5

def _firebase_app():
    try:
        app = get_app('acta-fcm-api')
    except ValueError:
        if not FIREBASE_PROJECT_ID:
            raise RuntimeError('Projeto Firebase não configurado')
        opcoes = {'projectId': FIREBASE_PROJECT_ID, 'httpTimeout': TIMEOUT_SECONDS}
        return initialize_app(options=opcoes, name='acta-fcm-api')

    if not FIREBASE_PROJECT_ID or app.project_id != FIREBASE_PROJECT_ID:
        raise RuntimeError('Projeto Firebase incompatível com a configuração da API')
    return app


def enviar_push(conn, id_usuario: int, fid_firebase: str, id_notificacao: int) -> str:
    try:
        mensagem = Message(
            data={'idNotificacao': str(id_notificacao)},
            android=AndroidConfig(priority='high'),
            fid=fid_firebase,
        )
        resposta = send(mensagem, app=_firebase_app())
        if not isinstance(resposta, str) or not resposta:
            raise FalhaEnvioPush('empty-firebase-response', recuperavel=True)
        return resposta
    except FalhaEnvioPush:
        raise
    except UnregisteredError as erro:
        try:
            limpar_fid_se_igual(conn, id_usuario, fid_firebase)
        except Exception as erro_limpeza:
            raise FalhaEnvioPush('unregistered-cleanup-failed', recuperavel=True, destino_invalido=True) from erro_limpeza
        raise FalhaEnvioPush('unregistered', recuperavel=False, destino_invalido=True) from erro
    except SenderIdMismatchError as erro:
        raise FalhaEnvioPush('sender-id-mismatch', recuperavel=False) from erro
    except FirebaseError as erro:
        codigo_bruto = str(getattr(erro, 'code', '') or type(erro).__name__).rsplit('/', 1)[-1].split(':', 1)[0].lower()
        codigo = ''.join(caractere for caractere in codigo_bruto if caractere.isascii() and (caractere.isalnum() or caractere in '-_'))[:64]
        codigo = codigo or type(erro).__name__.lower()
        temporarios = {
            'internal', 'unavailable', 'unknown', 'deadline-exceeded',
            'quota-exceeded', 'resource-exhausted', 'server-unavailable',
        }
        raise FalhaEnvioPush(codigo, recuperavel=codigo in temporarios) from erro
    except (RequestConnectionError, RequestTimeout) as erro:
        raise FalhaEnvioPush(type(erro).__name__.lower(), recuperavel=True) from erro
    except Exception as erro:
        raise FalhaEnvioPush(type(erro).__name__.lower(), recuperavel=False) from erro