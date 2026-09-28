from fastapi import FastAPI
from database import verificar_conexion


app = FastAPI(
    title="SFJPII AI",
    version="1.0.0"
)


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