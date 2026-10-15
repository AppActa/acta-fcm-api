from psycopg2.extras import RealDictCursor, execute_values
from app.schemas.notificacao import Notificacao

def listar(conn, id_usuario: int, apenas_nao_lidas: bool, categoria: str | None = None) -> list[Notificacao]:
    filtros = ['id_usuario_destino = %s', '(expira_em IS NULL OR expira_em > NOW())']
    parametros: list = [id_usuario]

    if apenas_nao_lidas:
        filtros.append('lido_em IS NULL')
    if categoria:
        filtros.append('categoria = %s')
        parametros.append(categoria)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT id, tipo, categoria, tipo_entidade, id_entidade, deep_link, criado_em, lido_em, expira_em
            FROM auditoria.notificacao
            WHERE {' AND '.join(filtros)}
            ORDER BY criado_em DESC, id DESC
            """, tuple(parametros),
        )
        return cursor.fetchall()

def contar_nao_lidas(conn, id_usuario: int) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) FROM auditoria.notificacao
            WHERE id_usuario_destino = %s AND lido_em IS NULL AND (expira_em IS NULL OR expira_em > NOW())
            """, (id_usuario,),
        )
        return cursor.fetchone()[0]

def marcar_lida(conn, id_usuario: int, id_notificacao: int) -> dict | None:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            UPDATE auditoria.notificacao SET lido_em = COALESCE(lido_em, NOW())
            WHERE id = %s AND id_usuario_destino = %s
            RETURNING id, tipo, categoria, tipo_entidade, id_entidade, deep_link, criado_em, lido_em, expira_em""",
            (id_notificacao, id_usuario),
        )
        linha = cursor.fetchone()
    conn.commit()
    return linha

def marcar_todas_lidas(conn, id_usuario: int) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE auditoria.notificacao SET lido_em = NOW()
            WHERE id_usuario_destino = %s AND lido_em IS NULL AND (expira_em IS NULL OR expira_em > NOW())""",
            (id_usuario,),
        )
        total = cursor.rowcount
    conn.commit()
    return total

def inserir_evento(conn, evento, tipo: str, categoria: str, destinatarios: list[int]) -> list[tuple[int, int]]:
    valores = [
        (
            id_usuario,
            evento.id_empresa,
            tipo,
            categoria,
            evento.tipo_entidade,
            evento.id_entidade,
            evento.deep_link,
            evento.chave_deduplicacao,
            evento.ocorrido_em,
        )
        for id_usuario in destinatarios
    ]
    with conn.cursor() as cursor:
        criadas = execute_values(
            cursor,
            """
            INSERT INTO auditoria.notificacao (id_usuario_destino, id_empresa, tipo, categoria, tipo_entidade, id_entidade, deep_link, chave_deduplicacao, criado_em)
            VALUES %s
            ON CONFLICT (id_usuario_destino, chave_deduplicacao) DO NOTHING
            RETURNING id, id_usuario_destino
            """,
            valores,
            fetch=True,
        )
    conn.commit()
    return criadas