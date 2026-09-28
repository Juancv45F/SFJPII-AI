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
    content: str,
    grafica=None
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
                            "content": content,
                            "grafica": grafica
                        }
                    ]
                }
            }
        },
        upsert=True
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
    coleccion.update_one({"admin_id": admin_id, "conversation_id": conversation_id}, {
        "$setOnInsert": {"admin_id": admin_id, "conversation_id": conversation_id, "createdAt": ahora},
        "$set": {"updatedAt": ahora},
        "$push": {"mensajes": {"$each": [
            {"role": "user", "content": mensaje},
            {"role": "assistant", "content": respuesta, "grafica": grafica}
        ]}}
    }, upsert=True)
