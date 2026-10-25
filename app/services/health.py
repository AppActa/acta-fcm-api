from contextlib import closing
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from httpx import Client, HTTPError
from psycopg2 import connect
from app.config import ACTA_PG_API_URL, DB_URL
from app.schemas.health import HealthResponse, HealthStatus
from app.services.fcm import _firebase_app

TIMEOUT_SECONDS = 5


def _verificar_banco() -> HealthStatus:
    try:
        with closing(connect(DB_URL, connect_timeout=TIMEOUT_SECONDS)) as conn:
            with conn.cursor() as cursor:
                cursor.execute('SET LOCAL statement_timeout = 5000')
                cursor.execute('SELECT 1')
                return 'UP' if cursor.fetchone() == (1,) else 'DOWN'
    except Exception:
        return 'DOWN'

def _verificar_auth() -> HealthStatus:
    try:
        with Client(timeout=TIMEOUT_SECONDS) as client:
            resposta = client.get(f'{ACTA_PG_API_URL.rstrip("/")}/health')
        return 'UP' if resposta.status_code == 200 and resposta.json().get('status') == 'UP' else 'DOWN'
    except (HTTPError, ValueError, AttributeError):
        return 'DOWN'

def _verificar_firebase() -> HealthStatus:
    try:
        credencial = _firebase_app().credential.get_credential()
        if not credencial.valid:
            transporte = Request()
            with closing(transporte.session):

                def requisicao(*args, **kwargs):
                    kwargs['timeout'] = TIMEOUT_SECONDS
                    return transporte(*args, **kwargs)

                credencial.refresh(requisicao)
        return 'UP' if credencial.valid else 'DOWN'
    except Exception:
        return 'DOWN'


def verificar_saude() -> HealthResponse:
    banco = _verificar_banco()
    auth = _verificar_auth()
    firebase = _verificar_firebase()
    status = 'UP' if banco == auth == firebase == 'UP' else 'DOWN'
    mensagem = ('O CATO verificou: API, banco de dados, Auth API e credenciais do Firebase estão funcionando!' if status == 'UP' else 'O CATO verificou: Um ou mais componentes estão indisponíveis...')
    return HealthResponse(status=status, banco=banco, auth=auth, firebase=firebase, mensagem=mensagem, verificado_em=datetime.now(timezone.utc).replace(microsecond=0))