from fastapi import APIRouter, Response

from app.schemas.health import HealthResponse
from app.services.health import verificar_saude

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "acta-fcm-api"}


@router.get(
    '/api/v1/health',
    response_model=HealthResponse,
    summary='Verifica a saúde da API e suas dependências',
    description='Consulta o banco, o health da Auth e a validade das credenciais Firebase. Não envia push nem comprova entrega de mensagens.',
    response_description='API, banco, Auth e credenciais Firebase disponíveis',
    responses={503: {'model': HealthResponse, 'description': 'Um ou mais componentes indisponíveis'}},
)
def health_dependencias(response: Response) -> HealthResponse:
    resultado = verificar_saude()
    response.status_code = 200 if resultado.status == 'UP' else 503
    return resultado