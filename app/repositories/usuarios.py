def listar_ids_ativos_da_empresa(conn, ids_usuarios: list[int], id_empresa: int) -> set[int]:
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT id FROM public.usuario_sistema
                WHERE id = ANY(%s) AND id_empresa = %s AND status = 'ATIVO'""",
            (ids_usuarios, id_empresa),
        )
        return {linha[0] for linha in cursor.fetchall()}

def atualizar_fid_firebase(conn, id_usuario: int, fid_firebase: str) -> bool:
    with conn.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_user_id', %s, true)", (str(id_usuario),))
        cursor.execute('UPDATE public.usuario_sistema SET firebase_fid = %s WHERE id = %s AND status = %s', (fid_firebase, id_usuario, 'ATIVO'),)

        if cursor.rowcount == 0:
            conn.rollback()
            return False
        
        cursor.execute('UPDATE public.usuario_sistema SET firebase_fid = NULL WHERE id <> %s AND firebase_fid = %s', (id_usuario, fid_firebase),)
    conn.commit()
    return True

def remover_fid_firebase(conn, id_usuario: int) -> None:
    with conn.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_user_id', %s, true)", (str(id_usuario),))
        cursor.execute('UPDATE public.usuario_sistema SET firebase_fid = NULL WHERE id = %s', (id_usuario,))
    conn.commit()

def obter_dados_push(conn, id_usuario: int) -> tuple[str | None, str | None]:
    with conn.cursor() as cursor:
        cursor.execute('SELECT nome, firebase_fid FROM public.usuario_sistema WHERE id = %s AND status = %s', (id_usuario, 'ATIVO'),)
        linha = cursor.fetchone()
    return (linha[0], linha[1]) if linha else (None, None)

def limpar_fid_se_igual(conn, id_usuario: int, fid_firebase: str) -> None:
    with conn.cursor() as cursor:
        cursor.execute('UPDATE public.usuario_sistema SET firebase_fid = NULL WHERE id = %s AND firebase_fid = %s', (id_usuario, fid_firebase),)
    conn.commit()