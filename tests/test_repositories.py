from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from psycopg2.extensions import adapt
from app.repositories import notificacoes, usuarios

class Cursor:
    def __init__(self, fetchall=(), fetchone=None, rowcount=1):
        self.resultado_lista = fetchall
        self.resultado_unico = fetchone
        self.rowcount = rowcount
        self.executados = []
        self.connection = SimpleNamespace(encoding='UTF8')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, parametros=None):
        self.executados.append((sql, parametros))

    def mogrify(self, sql, parametros):
        return sql % tuple(adapt(valor).getquoted() for valor in parametros)

    def fetchall(self):
        return self.resultado_lista

    def fetchone(self):
        return self.resultado_unico

class Connection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self, **kwargs):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

def test_listar_retorna_todas_filtrando_usuario_nao_lidas_e_categoria():
    cursor = Cursor(fetchall=[])
    conn = Connection(cursor)

    notificacoes.listar(conn, 123, True, 'PRAZO')

    sql, parametros = cursor.executados[0]
    assert 'id_usuario_destino = %s' in sql
    assert 'lido_em IS NULL' in sql
    assert 'categoria = %s' in sql
    assert 'LIMIT' not in sql
    assert '(criado_em, id) <' not in sql
    assert parametros == (123, 'PRAZO')

def test_marcar_lida_restringe_ao_destinatario_e_faz_commit():
    criado_em = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
    lido_em = datetime(2026, 10, 14, 13, tzinfo=timezone.utc)
    linha = {
        'id': 456, 'tipo': 'TAREFA_ATRIBUIDA', 'categoria': 'TAREFA',
        'tipo_entidade': 'TAREFA', 'id_entidade': '987', 'deep_link': 'acta://tarefas/987',
        'criado_em': criado_em, 'lido_em': lido_em, 'expira_em': None,
    }
    cursor = Cursor(fetchone=linha)
    conn = Connection(cursor)

    resposta = notificacoes.marcar_lida(conn, 123, 456)

    sql, parametros = cursor.executados[0]
    assert 'id = %s AND id_usuario_destino = %s' in sql
    assert parametros == (456, 123)
    assert resposta['id'] == 456
    assert conn.commits == 1

def test_atualizar_fid_limpa_associacao_anterior_e_faz_commit():
    cursor = Cursor(rowcount=1)
    conn = Connection(cursor)

    resultado = usuarios.atualizar_fid_firebase(conn, 123, 'fid-firebase-de-teste-123456')

    assert resultado is True
    assert len(cursor.executados) == 2
    assert 'SET firebase_fid = %s' in cursor.executados[0][0]
    assert 'id <> %s AND firebase_fid = %s' in cursor.executados[1][0]
    assert cursor.executados[1][1] == (123, 'fid-firebase-de-teste-123456')
    assert conn.commits == 1

def test_atualizar_fid_rejeita_usuario_inativo():
    cursor = Cursor(rowcount=0)
    conn = Connection(cursor)

    resultado = usuarios.atualizar_fid_firebase(conn, 123, 'fid-firebase-de-teste-123456')

    assert resultado is False
    assert conn.rollbacks == 1
    assert conn.commits == 0

@pytest.mark.parametrize('criadas', [[(456, 123), (457, 124)], [(457, 124)], []])
def test_inserir_evento_em_lote_retorna_somente_linhas_criadas(criadas):
    evento = SimpleNamespace(
        id_empresa=42, tipo_entidade='TAREFA', id_entidade='987',
        deep_link='acta://tarefas/987', chave_deduplicacao="tarefa:987:versao'3",
        ocorrido_em=datetime(2026, 10, 14, 12, tzinfo=timezone.utc),
    )
    cursor = Cursor(fetchall=criadas)
    conn = Connection(cursor)

    resultado = notificacoes.inserir_evento(conn, evento, 'TAREFA_ATRIBUIDA', 'TAREFA', [123, 124])

    assert resultado == criadas
    assert conn.commits == 1
    assert len(cursor.executados) == 1
    sql, _ = cursor.executados[0]
    assert b'ON CONFLICT (id_usuario_destino, chave_deduplicacao) DO NOTHING' in sql
    assert b'RETURNING id, id_usuario_destino' in sql
    assert b'(123,42,' in sql and b'(124,42,' in sql
    assert b"tarefa:987:versao''3" in sql

def test_inserir_evento_nao_confirma_lote_quando_banco_falha():
    evento = SimpleNamespace(
        id_empresa=42, tipo_entidade='TAREFA', id_entidade='987',
        deep_link='acta://tarefas/987', chave_deduplicacao='tarefa:987:v3',
        ocorrido_em=datetime(2026, 10, 14, 12, tzinfo=timezone.utc),
    )
    cursor = Cursor()
    conn = Connection(cursor)

    def falhar(*args):
        raise RuntimeError('banco indisponivel')

    cursor.execute = falhar
    with pytest.raises(RuntimeError):
        notificacoes.inserir_evento(conn, evento, 'TAREFA_ATRIBUIDA', 'TAREFA', [123, 124])

    assert conn.commits == 0 