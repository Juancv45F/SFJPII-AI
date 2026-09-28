from fastapi import FastAPI, Depends
from security import require_service_key
from database import verificar_conexion
from routes.test_tools import router as test_router
from routes.admin import router as admin_router


app = FastAPI(
    title="SFJPII AI",
    version="1.0.0"
)

# Routes

app.include_router(test_router, dependencies=[Depends(require_service_key)])
app.include_router(admin_router, dependencies=[Depends(require_service_key)])

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
        return {
            "status": "error",
            "mongodb": "disconnected",
            "detail": str(error)
        }