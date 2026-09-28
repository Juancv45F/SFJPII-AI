from config import settings
import secrets
from fastapi import Header, HTTPException


def require_service_key(x_service_key: str | None = Header(default=None)):
    # El backend de la farmacia valida usuario y rol antes de usar esta clave.
    expected = settings.sfjpii_ai_service_key
    if not expected:
        raise HTTPException(status_code=503, detail="Servicio no configurado")
    if not x_service_key or not secrets.compare_digest(x_service_key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Servicio no autorizado")
