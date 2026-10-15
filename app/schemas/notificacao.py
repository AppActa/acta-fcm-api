from datetime import datetime
from typing import TypedDict

class Notificacao(TypedDict): # verificador de tipos
    id: int
    tipo: str
    categoria: str
    tipo_entidade: str
    id_entidade: str
    deep_link: str
    criado_em: datetime
    lido_em: datetime | None
    expira_em: datetime | None