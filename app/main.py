from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.error_handlers import tratar_erro_inesperado, tratar_http_exception, tratar_validacao
from app.routes.router import api_router

app = FastAPI(
    title="ACTA FCM API",
    description="Central de notificações e integração com Firebase Cloud Messaging.",
    version="1.0",
)

app.add_exception_handler(StarletteHTTPException, tratar_http_exception)
app.add_exception_handler(RequestValidationError, tratar_validacao)
app.add_exception_handler(Exception, tratar_erro_inesperado)
app.include_router(api_router)