from fastapi import APIRouter, HTTPException

from schemas.chat import ChatRequest, ChatResponse
from agents.admin_agent import procesar_mensaje_admin


router = APIRouter(
    prefix="/admin",
    tags=["Admin AI"]
)


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat_admin(request: ChatRequest):
    try:
        return procesar_mensaje_admin(
            request.mensaje
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="No se pudo completar la consulta"
        )