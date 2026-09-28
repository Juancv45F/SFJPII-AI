from fastapi import APIRouter, HTTPException, Header

from schemas.chat import ChatRequest, ChatResponse
from agents.admin_agent import procesar_mensaje_admin
from services.conversation_service import crear_conversation_id


router = APIRouter(
    prefix="/admin",
    tags=["Admin AI"]
)


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat_admin(
    request: ChatRequest,
    x_admin_id: str = Header(...)
):
    try:
        conversation_id = (
            request.conversation_id
            or crear_conversation_id()
        )

        return procesar_mensaje_admin(
            mensaje=request.mensaje,
            conversation_id=conversation_id,
            admin_id=x_admin_id
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No se pudo completar la consulta"
        )