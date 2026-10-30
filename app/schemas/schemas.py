from datetime import datetime
from pydantic import AwareDatetime, ConfigDict, Field, PositiveInt
from app.schemas.base import ModeloACTA

class FalhaEnvioPush(Exception):
    def __init__(self, codigo: str, recuperavel: bool, destino_invalido: bool = False):
        super().__init__(codigo)
        self.codigo = codigo
        self.recuperavel = recuperavel
        self.destino_invalido = destino_invalido

class EventoNotificacao(ModeloACTA):
    model_config = ConfigDict(extra='forbid')

    id_evento: str = Field(min_length=1, max_length=100)
    tipo_evento: str = Field(min_length=1, max_length=60)
    ocorrido_em: AwareDatetime
    id_empresa: PositiveInt
    ids_destinatarios: list[PositiveInt] = Field(min_length=1, max_length=100)
    tipo_entidade: str = Field(min_length=1, max_length=40)
    id_entidade: str = Field(min_length=1, max_length=100)
    deep_link: str = Field(min_length=1, max_length=240)
    chave_deduplicacao: str = Field(min_length=1, max_length=160)

class EventoNotificacaoResponse(ModeloACTA):
    quantidade_criada: int
    quantidade_duplicada: int

class NotificacaoResponse(ModeloACTA):
    id: int
    tipo: str
    categoria: str
    tipo_entidade: str
    id_entidade: str
    deep_link: str
    criado_em: datetime
    lido_em: datetime | None
    expira_em: datetime | None

class FidDispositivoInput(ModeloACTA):
    model_config = ConfigDict(extra='forbid')
    fid_firebase: str = Field(min_length=1, max_length=128)

class UsuarioAutenticado(ModeloACTA):
    id_usuario: PositiveInt
    id_empresa: PositiveInt

class ErroResponse(ModeloACTA):
    mensagens: list[str]
    http_status: int
    timestamp: datetime = Field(default_factory=datetime.now)