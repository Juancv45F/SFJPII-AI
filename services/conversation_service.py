from uuid import uuid4


_conversaciones: dict[str, list[dict]] = {}


def crear_conversation_id() -> str:
    return str(uuid4())


def obtener_historial(conversation_id: str) -> list[dict]:
    return _conversaciones.get(conversation_id, [])


def agregar_mensaje(
    conversation_id: str,
    role: str,
    content: str
):
    if conversation_id not in _conversaciones:
        _conversaciones[conversation_id] = []

    _conversaciones[conversation_id].append({
        "role": role,
        "content": content
    })

    # Evitamos que crezca indefinidamente.
    _conversaciones[conversation_id] = (
        _conversaciones[conversation_id][-12:]
    )


def borrar_conversacion(conversation_id: str):
    _conversaciones.pop(conversation_id, None)