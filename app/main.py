from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.error_handlers import tratar_erro_inesperado, tratar_http_exception, tratar_validacao
from app.routes.router import api_router
from app.schemas.schemas import ErroResponse

app = FastAPI(
    title="ACTA FCM API",
    description="Central de notificações e integração com Firebase Cloud Messaging.",
    version="1.0",
    docs_url="/api/v1/me/docs",
    redoc_url="/api/v1/me/redoc",
    openapi_url="/api/v1/me/openapi.json",
    swagger_ui_oauth2_redirect_url="/api/v1/me/docs/oauth2-redirect",
    responses={
        400: {"model": ErroResponse, "description": "Parâmetros ou corpo inválidos"},
        "4XX": {"model": ErroResponse, "description": "Erro de requisição, autenticação ou regra de negócio"},
    },
)

app.add_exception_handler(StarletteHTTPException, tratar_http_exception)
app.add_exception_handler(RequestValidationError, tratar_validacao)
app.add_exception_handler(Exception, tratar_erro_inesperado)
app.include_router(api_router)

@app.get("/docs", include_in_schema=False)
def redirecionar_documentacao():
    return RedirectResponse(url="/api/v1/me/docs", status_code=307)