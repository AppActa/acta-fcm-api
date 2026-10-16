from datetime import date
from psycopg2.extras import RealDictCursor

_TAREFAS_ELEGIVEIS = """
    SELECT t.id, t.id_responsavel, t.data_fim_prevista, c.id_empresa
    FROM pdca.tarefa t
    JOIN pdca.plano_acao pa ON pa.id = t.id_plano_acao
    JOIN pdca.ciclo c ON c.id = pa.id_ciclo
    JOIN public.empresa e ON e.id = c.id_empresa
    JOIN public.usuario_sistema u ON u.id = t.id_responsavel
    WHERE t.data_fim_prevista = %s
      AND t.status NOT IN ('CONCLUIDA', 'CANCELADA')
      AND pa.status NOT IN ('CONCLUIDO', 'CANCELADO')
      AND c.status NOT IN ('CONCLUIDO', 'CANCELADO', 'PAUSADO')
      AND e.status = 'ATIVO'
      AND u.status = 'ATIVO' AND u.id_empresa = c.id_empresa
"""

def listar_candidatos(conn, data_prazo: date, apos_id: int, limite: int = 100) -> list:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(_TAREFAS_ELEGIVEIS + ' AND t.id > %s ORDER BY t.id LIMIT %s', (data_prazo, apos_id, limite))
        return cursor.fetchall()

def obter_candidato(conn, data_prazo: date, id_tarefa: int) -> dict | None:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(_TAREFAS_ELEGIVEIS + ' AND t.id = %s', (data_prazo, id_tarefa))
        return cursor.fetchone()