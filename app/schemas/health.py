from typing import Literal
from pydantic import AwareDatetime
from app.schemas.base import ModeloACTA

HealthStatus = Literal['UP', 'DOWN']

class HealthResponse(ModeloACTA):
    status: HealthStatus
    banco: HealthStatus
    auth: HealthStatus
    firebase: HealthStatus
    mensagem: str
    verificado_em: AwareDatetime