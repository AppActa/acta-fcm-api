from collections.abc import Generator
from fastapi import HTTPException
from psycopg2 import connect
from psycopg2.extensions import connection
from app.config import DB_URL

def get_conn() -> Generator[connection, None, None]:
    try:
        conn = connect(DB_URL)
    except Exception as e:
        raise HTTPException(status_code=503, detail='Erro no banco de dados') from e

    try:
        yield conn
    finally:
        conn.close()