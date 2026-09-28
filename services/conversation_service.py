from uuid import uuid4
from datetime import datetime, timezone, timedelta
from pymongo import ASCENDING, DESCENDING

from database import db
from config import settings


coleccion = db.conversaciones_ai


def preparar_indices_conversaciones():

    # Administradores
    coleccion.create_index([("admin_id", ASCENDING), ("conversation_id", ASCENDING)],
                           unique=True, name="admin_conversation_unique")
    coleccion.create_index([("admin_id", ASCENDING), ("updatedAt", DESCENDING)],
                           name="admin_updated_desc")
    coleccion.create_index("expiresAt", expireAfterSeconds=0, name="conversation_expiration")

    #Clientes
    coleccion.create_index(
        [
            ("user_id", ASCENDING),
            ("conversation_id", ASCENDING)
        ],
        unique=True,
        sparse=True,
        name="user_conversation_unique"
    )

    coleccion.create_index(
        [
            ("user_id", ASCENDING),
            ("updatedAt", DESCENDING)
        ],
        sparse=True,
        name="user_updated_desc"
    )


def _expiracion(ahora):
    return ahora + timedelta(days=settings.chat_retention_days) if settings.chat_retention_days > 0 else None


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


def borrar_conversacion(
    admin_id: str,
    conversation_id: str
):
    resultado = coleccion.delete_one(
        {
            "admin_id": admin_id,
            "conversation_id": conversation_id
        }
    )
    return resultado.deleted_count == 1

def listar_conversaciones(admin_id: str, offset: int = 0):
    documentos = coleccion.find({"admin_id": admin_id}, {
        "_id": 0, "conversation_id": 1, "createdAt": 1, "updatedAt": 1,
        "mensajes": {"$slice": 1}
    }).sort([("updatedAt", -1), ("conversation_id", 1)]).skip(offset).limit(31)
    items = list(documentos)
    return {"items": [{"conversation_id": d["conversation_id"],
        "titulo": next((m["content"][:100] for m in d.get("mensajes", []) if m.get("role") == "user"), "Consulta"),
        "updatedAt": d.get("updatedAt"), "createdAt": d.get("createdAt")}
        for d in items[:30]], "has_more": len(items) > 30}


def recuperar_conversacion(admin_id: str, conversation_id: str):
    return coleccion.find_one({"admin_id": admin_id, "conversation_id": conversation_id},
                             {"_id": 0, "admin_id": 0})


def guardar_turno(admin_id: str, conversation_id: str, mensaje: str, respuesta: str, grafica=None):
    ahora = datetime.now(timezone.utc)
    campos = {"updatedAt": ahora}
    expiracion = _expiracion(ahora)
    if expiracion is not None:
        campos["expiresAt"] = expiracion
    coleccion.update_one({"admin_id": admin_id, "conversation_id": conversation_id}, {
        "$setOnInsert": {"admin_id": admin_id, "conversation_id": conversation_id, "createdAt": ahora},
        "$set": campos,
        **({"$unset": {"expiresAt": ""}} if expiracion is None else {}),
        "$push": {"mensajes": {"$each": [
            {"role": "user", "content": mensaje},
            {"role": "assistant", "content": respuesta, "grafica": grafica}
        ]}}
    }, upsert=True)

def obtener_historial_cliente(
    user_id: str,
    conversation_id: str
) -> list[dict]:

    conversacion = coleccion.find_one(
        {
            "tipo_usuario": "cliente",
            "user_id": user_id,
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

def guardar_turno_cliente(
    user_id: str,
    conversation_id: str,
    mensaje: str,
    respuesta: str
):
    ahora = datetime.now(timezone.utc)

    campos = {
        "updatedAt": ahora
    }

    expiracion = _expiracion(ahora)

    if expiracion is not None:
        campos["expiresAt"] = expiracion

    coleccion.update_one(
        {
            "tipo_usuario": "cliente",
            "user_id": user_id,
            "conversation_id": conversation_id
        },
        {
            "$setOnInsert": {
                "tipo_usuario": "cliente",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "createdAt": ahora
            },
            "$set": campos,

            **(
                {
                    "$unset": {
                        "expiresAt": ""
                    }
                }
                if expiracion is None
                else {}
            ),

            "$push": {
                "mensajes": {
                    "$each": [
                        {
                            "role": "user",
                            "content": mensaje
                        },
                        {
                            "role": "assistant",
                            "content": respuesta
                        }
                    ]
                }
            }
        },
        upsert=True
    )