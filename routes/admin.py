from fastapi import APIRouter, HTTPException, Header, Query

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

@router.get("/conversations")
def conversations(x_admin_id: str = Header(...), offset: int = Query(0, ge=0, le=100000)):
    from services.conversation_service import listar_conversaciones
    return listar_conversaciones(x_admin_id, offset)


@router.get("/conversations/{conversation_id}")
def conversation(conversation_id: str, x_admin_id: str = Header(...)):
    from services.conversation_service import recuperar_conversacion
    result = recuperar_conversacion(x_admin_id, conversation_id)
    if not result:
        raise HTTPException(404, "Conversación no encontrada")
    return result


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, x_admin_id: str = Header(...)):
    from services.conversation_service import borrar_conversacion
    if not borrar_conversacion(x_admin_id, conversation_id):
        raise HTTPException(404, "Conversación no encontrada")
