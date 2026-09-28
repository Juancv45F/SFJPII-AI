from fastapi import (
    APIRouter,
    Header,
    HTTPException
)
from bson import ObjectId
from openai import APIConnectionError, APITimeoutError, RateLimitError
from pymongo.errors import PyMongoError

from schemas.chat import (
    ChatRequest,
    ChatResponse
)

from agents.cliente_agent import (
    procesar_mensaje_cliente
)

from services.conversation_service import (
    crear_conversation_id
)
from logging_setup import get_logger
from tools.validators import ToolValidationError


logger = get_logger("sfjpii.ai.cliente")


router = APIRouter(
    prefix="/cliente",
    tags=["Cliente AI"]
)


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat_cliente(
    request: ChatRequest,
    x_user_id: str = Header(...)
):
    if not ObjectId.is_valid(x_user_id):
        raise HTTPException(status_code=400, detail="Identidad de cliente no válida")

    try:
        conversation_id = (
            request.conversation_id
            or crear_conversation_id()
        )

        return procesar_mensaje_cliente(
            mensaje=request.mensaje,
            conversation_id=conversation_id,
            user_id=x_user_id
        )

    except ToolValidationError as error:
        logger.warning("client_chat_validation_failed", extra={
            "user_id": x_user_id,
            "conversation_id": request.conversation_id,
            "error_type": type(error).__name__,
        })
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except RateLimitError:
        raise HTTPException(status_code=429, detail="El servicio de IA está temporalmente saturado")

    except APITimeoutError:
        raise HTTPException(status_code=504, detail="La consulta tardó demasiado")

    except (APIConnectionError, PyMongoError) as error:
        logger.exception("client_chat_dependency_failed", extra={
            "user_id": x_user_id,
            "conversation_id": request.conversation_id,
            "error_type": type(error).__name__,
        })
        raise HTTPException(status_code=503, detail="Un servicio de datos no está disponible")

    except Exception as error:
        logger.exception("client_chat_failed", extra={
            "user_id": x_user_id,
            "conversation_id": request.conversation_id,
            "error_type": type(error).__name__,
        })
        raise HTTPException(
            status_code=500,
            detail="No se pudo completar la consulta"
        )
