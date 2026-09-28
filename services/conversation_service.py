from uuid import uuid4
from datetime import datetime, timezone

from database import db


coleccion = db.conversaciones_ai


def crear_conversation_id() -> str:
    return str(uuid4())


def obtener_historial(
    admin_id: str,
    conversation_id: str
) -> list[dict]:

    conversacion = coleccion.find_one(
        {
            "admin_id": admin_id,
            "conversation_id": conversation_id
        },
        {
            "_id": 0,
            "mensajes": 1
        }
    )

    if not conversacion:
        return []

    return conversacion.get(
        "mensajes",
        []
    )


def agregar_mensaje(
    admin_id: str,
    conversation_id: str,
    role: str,
    content: str
):
    ahora = datetime.now(timezone.utc)

    coleccion.update_one(
        {
            "admin_id": admin_id,
            "conversation_id": conversation_id
        },
        {
            "$setOnInsert": {
                "admin_id": admin_id,
                "conversation_id": conversation_id,
                "createdAt": ahora
            },
            "$set": {
                "updatedAt": ahora
            },
            "$push": {
                "mensajes": {
                    "$each": [
                        {
                            "role": role,
                            "content": content
                        }
                    ],
                    "$slice": -12
                }
            }
        },
        upsert=True
    )


def borrar_conversacion(
    admin_id: str,
    conversation_id: str
):
    coleccion.delete_one(
        {
            "admin_id": admin_id,
            "conversation_id": conversation_id
        }
    )