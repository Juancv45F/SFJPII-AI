from uuid import uuid4


_conversaciones: dict[str, list[dict]] = {}


def crear_conversation_id() -> str:
    return str(uuid4())


def _crear_clave(
    admin_id: str,
    conversation_id: str
) -> str:
    return f"{admin_id}:{conversation_id}"


def obtener_historial(
    admin_id: str,
    conversation_id: str
) -> list[dict]:

    clave = _crear_clave(
        admin_id,
        conversation_id
    )

    return _conversaciones.get(
        clave,
        []
    ).copy()


def agregar_mensaje(
    admin_id: str,
    conversation_id: str,
    role: str,
    content: str
):
    clave = _crear_clave(
        admin_id,
        conversation_id
    )

    if clave not in _conversaciones:
        _conversaciones[clave] = []

    _conversaciones[clave].append({
        "role": role,
        "content": content
    })

    # Conservamos los últimos 12 mensajes.
    _conversaciones[clave] = (
        _conversaciones[clave][-12:]
    )


def borrar_conversacion(
    admin_id: str,
    conversation_id: str
):
    clave = _crear_clave(
        admin_id,
        conversation_id
    )

    _conversaciones.pop(
        clave,
        None
    )