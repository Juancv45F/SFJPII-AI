from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from security import require_service_key
from database import verificar_conexion
from services.conversation_service import asegurar_indices_conversaciones
from logging_setup import get_logger
from routes.test_tools import router as test_router
from routes.admin import router as admin_router
from routes.cliente import router as cliente_router

logger = get_logger("sfjpii.ai")


@asynccontextmanager
async def lifespan(_app):
    # No debe impedir el arranque: si falla se reintenta al guardar un turno.
    asegurar_indices_conversaciones()
    yield


app = FastAPI(
    title="SFJPII AI",
    version="1.0.0",
    lifespan=lifespan,
    # Servicio interno: su esquema no debe publicarse sin X-Service-Key.
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Routes

app.include_router(test_router, dependencies=[Depends(require_service_key)])
app.include_router(admin_router, dependencies=[Depends(require_service_key)])
app.include_router(cliente_router, dependencies=[Depends(require_service_key)])

# --------------------------------
@app.get("/")
def root():
    return {
        "service": "SFJPII-AI",
        "status": "running"
    }


@app.get("/health")
def health():
    # Público: no revela dependencias ni genera carga en MongoDB.
    return {"status": "ok"}


@app.get("/health/deep", dependencies=[Depends(require_service_key)])
def health_deep():
    try:
        verificar_conexion()

    except Exception as error:
        logger.exception("health_check_failed", extra={"error_type": type(error).__name__})
        raise HTTPException(status_code=503, detail="Un servicio de datos no está disponible")

    return {
        "status": "ok",
        "mongodb": "connected"
    }
