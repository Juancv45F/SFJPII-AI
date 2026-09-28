from openai import OpenAI

from config import settings


client = OpenAI(
    api_key=settings.openai_api_key
)


def crear_respuesta_admin(
    mensaje: str,
    instrucciones: str,
    tools: list
):
    return client.responses.create(
        model=settings.openai_model,
        instructions=instrucciones,
        input=mensaje,
        tools=tools,
        store=True
    )


def continuar_respuesta_admin(
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