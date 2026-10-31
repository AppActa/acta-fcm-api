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

TITULOS_PUSH = {
    'TAREFA_ATRIBUIDA': 'Nova tarefa atribuída',
    'TAREFA_REATRIBUIDA': 'Tarefa reatribuída',
    'TAREFA_VENCE_AMANHA': 'Tarefa vence amanhã',
    'TAREFA_ATRASADA': 'Tarefa atrasada',
    'CICLO_MEMBRO_ADICIONADO': 'Você foi adicionado a um ciclo',
    'CICLO_PAUSADO': 'Ciclo pausado',
    'CICLO_CANCELADO': 'Ciclo cancelado',
    'TREINAMENTO_ATRIBUIDO': 'Treinamento atribuído',
    'TREINAMENTO_LEMBRETE': 'Treinamento pendente',
    'FORMULARIO_PUBLICADO': 'Novo formulário disponível',
    'FORMULARIO_LEMBRETE': 'Formulário pendente',
    'IMPORTACAO_FALHOU': 'Falha na importação',
}

MENSAGENS_PUSH = {
    'TAREFA_ATRIBUIDA': 'Você recebeu uma nova tarefa.',
    'TAREFA_REATRIBUIDA': 'Uma tarefa foi reatribuída para você.',
    'TAREFA_VENCE_AMANHA': 'Uma tarefa sua vence amanhã.',
    'TAREFA_ATRASADA': 'Uma tarefa sua está atrasada.',
    'CICLO_MEMBRO_ADICIONADO': 'Você pode acompanhar as atualizações deste ciclo.',
    'CICLO_PAUSADO': 'Um ciclo do qual você participa foi pausado.',
    'CICLO_CANCELADO': 'Um ciclo do qual você participa foi cancelado.',
    'TREINAMENTO_ATRIBUIDO': 'Um treinamento foi atribuído a você.',
    'TREINAMENTO_LEMBRETE': 'Você tem um treinamento pendente.',
    'FORMULARIO_PUBLICADO': 'Um novo formulário está disponível para você.',
    'FORMULARIO_LEMBRETE': 'Você tem um formulário pendente de resposta.',
    'IMPORTACAO_FALHOU': 'Uma importação falhou. Acesse o ACTA para verificar.',
}