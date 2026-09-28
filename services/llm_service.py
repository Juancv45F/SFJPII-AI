from openai import OpenAI

from config import settings


client = OpenAI(
    api_key=settings.openai_api_key
)


def crear_respuesta(
    mensaje: str,
    historial: list,
    instrucciones: str,
    tools: list
):
    mensajes = []

    # Agregamos el historial de la conversación.
    for item in historial:
        mensajes.append({
            "role": item["role"],
            "content": item["content"]
        })

    # Agregamos el mensaje actual.
    mensajes.append({
        "role": "user",
        "content": mensaje
    })

    return client.responses.create(
        model=settings.openai_model,
        instructions=instrucciones,
        input=mensajes,
        tools=tools,
        store=True
    )


def continuar_respuesta(
    response_id: str,
    tool_outputs: list,
    instrucciones: str,
    tools: list
):
    return client.responses.create(
        model=settings.openai_model,
        instructions=instrucciones,
        previous_response_id=response_id,
        input=tool_outputs,
        tools=tools,
        store=True
    )