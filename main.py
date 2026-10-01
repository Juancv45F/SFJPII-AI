from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from security import require_service_key
from database import verificar_conexion
from services.conversation_service import preparar_indices_conversaciones
from logging_setup import get_logger
from routes.test_tools import router as test_router
from routes.admin import router as admin_router
from routes.cliente import router as cliente_router
from services.keep_alive_service import start_keep_alive_task, stop_keep_alive_task

logger = get_logger("sfjpii.ai")


@asynccontextmanager
async def lifespan(_app):
    preparar_indices_conversaciones()
    logger.info("conversation_indexes_ready", extra={"operation": "startup"})
    keep_alive_task = start_keep_alive_task()
    try:
        yield
    finally:
        await stop_keep_alive_task(keep_alive_task)


app = FastAPI(
    title="SFJPII AI",
    version="1.0.0",
    lifespan=lifespan
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
    try:
        verificar_conexion()

        return {
            "status": "ok",
            "mongodb": "connected"
        }

    except Exception as error:
        logger.exception("health_check_failed", extra={"error_type": type(error).__name__})
        return {
            "status": "error",
            "mongodb": "disconnected"
        }
