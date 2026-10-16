from fastapi import APIRouter
from app.routes import dispositivo, eventos, health, notificacoes

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(notificacoes.router)
api_router.include_router(eventos.router)
api_router.include_router(dispositivo.router)