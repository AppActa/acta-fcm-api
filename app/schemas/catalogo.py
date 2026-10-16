TIPOS_EVENTO = {
    # codigo do evento: (categoria: eh_push)
    'TAREFA_ATRIBUIDA': ('TAREFA', True),
    'TAREFA_REATRIBUIDA': ('TAREFA', True),
    'TAREFA_VENCE_AMANHA': ('PRAZO', True),
    'TAREFA_ATRASADA': ('PRAZO', True),
    'TAREFA_BLOQUEADA': ('TAREFA', False),
    'TAREFA_DESBLOQUEADA': ('TAREFA', False),
    'CICLO_MEMBRO_ADICIONADO': ('CICLO', True),
    'CICLO_PAUSADO': ('CICLO', True),
    'CICLO_CANCELADO': ('CICLO', True),
    'CICLO_CONCLUIDO': ('CICLO', False),
    'TREINAMENTO_ATRIBUIDO': ('TREINAMENTO', True),
    'TREINAMENTO_LEMBRETE': ('TREINAMENTO', True),
    'FORMULARIO_PUBLICADO': ('FORMULARIO', True),
    'FORMULARIO_LEMBRETE': ('FORMULARIO', True),
    'FORMULARIO_RESPONDIDO': ('FORMULARIO', False),
    'IMPORTACAO_FALHOU': ('IMPORTACAO', True),
    'LICAO_APRENDIDA': ('APRENDIZADO', False),
}

CATEGORIAS_NOTIFICACAO = frozenset(categoria for categoria, _ in TIPOS_EVENTO.values())

ENTIDADE_POR_CATEGORIA = {
    'TAREFA': 'TAREFA',
    'PRAZO': 'TAREFA',
    'CICLO': 'CICLO',
    'TREINAMENTO': 'TREINAMENTO',
    'FORMULARIO': 'FORMULARIO',
    'IMPORTACAO': 'IMPORTACAO',
    'APRENDIZADO': 'LICAO_APRENDIDA',
}

ROTAS_ENTIDADE = {
    'TAREFA': 'tarefas',
    'CICLO': 'ciclos',
    'TREINAMENTO': 'treinamentos',
    'FORMULARIO': 'formularios',
    'IMPORTACAO': 'importacoes',
    'LICAO_APRENDIDA': 'licoes',
}

MENSAGENS_PUSH = {
    'TAREFA_ATRIBUIDA': 'Uma tarefa foi atribuída a você.',
    'TAREFA_REATRIBUIDA': 'Uma tarefa foi reatribuída para você.',
    'TAREFA_VENCE_AMANHA': 'Você tem uma tarefa com prazo para amanhã.',
    'TAREFA_ATRASADA': 'Você tem uma tarefa com prazo vencido.',
    'CICLO_MEMBRO_ADICIONADO': 'Você foi incluído em um ciclo.',
    'CICLO_PAUSADO': 'Um ciclo do qual você participa foi pausado.',
    'CICLO_CANCELADO': 'Um ciclo do qual você participa foi cancelado.',
    'TREINAMENTO_ATRIBUIDO': 'Um treinamento foi atribuído a você.',
    'TREINAMENTO_LEMBRETE': 'Você tem um treinamento pendente.',
    'FORMULARIO_PUBLICADO': 'Um novo formulário está disponível para você.',
    'FORMULARIO_LEMBRETE': 'Você tem um formulário pendente de resposta.',
    'IMPORTACAO_FALHOU': 'Uma importação falhou. Acesse o ACTA para verificar.',
}