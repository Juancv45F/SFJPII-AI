from time import monotonic
from types import SimpleNamespace

from openai import APITimeoutError, OpenAI

from config import settings


client = OpenAI(
    api_key=settings.ai_api_key,
    base_url=settings.ai_base_url,
    # El valor por defecto del SDK (10 min, 2 reintentos) supera maxDuration.
    timeout=settings.ai_request_timeout_seconds,
    max_retries=1
)


def _convertir_tools(tools: list) -> list:
    # "strict" se omite: DeepSeek solo lo admite en su endpoint beta y en
    # OpenAI es opcional.
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        }
        for tool in tools
    ]


def _completar(mensajes: list, instrucciones: str, tools: list, limite: float):
    # El límite es del turno completo: las rondas de tools no pueden sumar más
    # que maxDuration. Las rutas convierten este error en un 504 controlado.
    restante = limite - monotonic()
    if restante <= 0:
        raise APITimeoutError(request=None)

    opciones = {"timeout": min(settings.ai_request_timeout_seconds, restante)}

    # Sin tope, un mensaje de cliente puede pedir la salida máxima del modelo
    # en cada ronda de tools. OpenAI usa otro nombre para este parámetro.
    parametro_tope = "max_completion_tokens" if settings.ai_provider == "openai" else "max_tokens"
    opciones[parametro_tope] = settings.ai_max_output_tokens

    # DeepSeek piensa por defecto y, con tools, exigiría reenviar
    # reasoning_content en todo el historial, que no se guarda.
    if settings.ai_provider == "deepseek":
        opciones["extra_body"] = {"thinking": {"type": "disabled"}}

    # Desde GPT-5.4, Chat Completions solo admite tools con reasoning_effort
    # "none", y el valor por defecto de la API es "medium".
    if settings.ai_provider == "openai" and settings.ai_reasoning_effort != "off":
        opciones["reasoning_effort"] = settings.ai_reasoning_effort

    completion = client.chat.completions.create(
        model=settings.ai_model,
        messages=[{"role": "system", "content": instrucciones}, *mensajes],
        tools=_convertir_tools(tools),
        **opciones
    )

    mensaje = completion.choices[0].message
    llamadas = mensaje.tool_calls or []
    asistente = {
        "role": "assistant",
        "content": mensaje.content or ""
    }

    if llamadas:
        asistente["tool_calls"] = [
            {
                "id": llamada.id,
                "type": "function",
                "function": {
                    "name": llamada.function.name,
                    "arguments": llamada.function.arguments
                }
            }
            for llamada in llamadas
        ]

    # Chat Completions no guarda estado: la respuesta lleva la conversación
    # acumulada para poder continuarla tras ejecutar las tools.
    return SimpleNamespace(
        id=completion.id,
        output=[
            SimpleNamespace(
                type="function_call",
                name=llamada.function.name,
                arguments=llamada.function.arguments,
                call_id=llamada.id
            )
            for llamada in llamadas
        ],
        output_text=mensaje.content or "",
        mensajes=[*mensajes, asistente],
        limite=limite
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

    limite = monotonic() + settings.ai_turn_timeout_seconds

    return _completar(mensajes, instrucciones, tools, limite)


def continuar_respuesta(
    response,
    tool_outputs: list,
    instrucciones: str,
    tools: list
):
    mensajes = [
        *response.mensajes,
        *[
            {
                "role": "tool",
                "tool_call_id": tool_output["call_id"],
                "content": tool_output["output"]
            }
            for tool_output in tool_outputs
        ]
    ]

    return _completar(mensajes, instrucciones, tools, response.limite)
