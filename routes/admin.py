from fastapi import APIRouter, HTTPException, Header, Query, Path
from openai import APIConnectionError, APITimeoutError, RateLimitError
from pymongo.errors import PyMongoError

from schemas.chat import ChatRequest, ChatResponse
from agents.admin_agent import procesar_mensaje_admin
from services.conversation_service import crear_conversation_id
from tools.validators import ToolValidationError
from logging_setup import get_logger


logger = get_logger("sfjpii.ai.admin")


def _log_error(evento, error, admin_id=None, conversation_id=None):
    logger.exception(evento, extra={"admin_id": admin_id, "conversation_id": conversation_id,
                                    "error_type": type(error).__name__})


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

    except ToolValidationError as error:
        logger.warning("admin_chat_validation_failed", extra={"admin_id": x_admin_id,
                       "conversation_id": request.conversation_id, "error_type": type(error).__name__})
        raise HTTPException(status_code=422, detail=str(error))
    except RateLimitError as error:
        _log_error("admin_chat_rate_limited", error, x_admin_id, request.conversation_id)
        raise HTTPException(status_code=429, detail="El servicio de IA está temporalmente saturado")
    except APITimeoutError as error:
        _log_error("admin_chat_timeout", error, x_admin_id, request.conversation_id)
        raise HTTPException(status_code=504, detail="La consulta tardó demasiado")
    except (APIConnectionError, PyMongoError) as error:
        _log_error("admin_chat_dependency_failed", error, x_admin_id, request.conversation_id)
        raise HTTPException(status_code=503, detail="Un servicio de datos no está disponible")
    except Exception as error:
        _log_error("admin_chat_failed", error, x_admin_id, request.conversation_id)
        raise HTTPException(
            status_code=500,
            detail="No se pudo completar la consulta"
        )

@router.get("/conversations")
def conversations(x_admin_id: str = Header(...), offset: int = Query(0, ge=0, le=100000)):
    from services.conversation_service import listar_conversaciones
    try:
        return listar_conversaciones(x_admin_id, offset)
    except PyMongoError as error:
        _log_error("conversation_list_failed", error, x_admin_id)
        raise HTTPException(503, "No se pudo consultar el historial")


@router.get("/conversations/{conversation_id}")
def conversation(conversation_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]{1,128}$"), x_admin_id: str = Header(...)):
    from services.conversation_service import recuperar_conversacion
    try:
        result = recuperar_conversacion(x_admin_id, conversation_id)
    except PyMongoError as error:
        _log_error("conversation_read_failed", error, x_admin_id, conversation_id)
        raise HTTPException(503, "No se pudo consultar la conversación")
    if not result:
        raise HTTPException(404, "Conversación no encontrada")
    return result


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]{1,128}$"), x_admin_id: str = Header(...)):
    from services.conversation_service import borrar_conversacion
    try:
        deleted = borrar_conversacion(x_admin_id, conversation_id)
    except PyMongoError as error:
        _log_error("conversation_delete_failed", error, x_admin_id, conversation_id)
        raise HTTPException(503, "No se pudo eliminar la conversación")
    if not deleted:
        raise HTTPException(404, "Conversación no encontrada")
