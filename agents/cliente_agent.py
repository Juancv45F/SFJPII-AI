import json

from prompts.cliente import obtener_cliente_prompt

from services.cliente_tools import (
    CLIENTE_TOOLS,
    ejecutar_cliente_tool
)

from services.conversation_service import (
    obtener_historial_cliente,
    guardar_turno_cliente
)

from services.llm_service import (
    crear_respuesta,
    continuar_respuesta
)


def procesar_mensaje_cliente(
    mensaje: str,
    conversation_id: str,
    user_id: str
):
    # Recuperar historial de esta conversación
    historial = obtener_historial_cliente(
        user_id,
        conversation_id
    )

    # Prompt exclusivo para clientes
    instrucciones = obtener_cliente_prompt()

    # Primera petición al modelo
    response = crear_respuesta(
        mensaje=mensaje,
        historial=[
            {
                "role": m["role"],
                "content": m["content"]
            }
            for m in historial[-12:]
        ],
        instrucciones=instrucciones,
        tools=CLIENTE_TOOLS
    )

    tools_utilizadas = []

    # Permitimos varias rondas de tools.
    # Ejemplo:
    # "¿Cuánto cuestan el shampoo y los pañales?"
    for _ in range(6):

        function_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # Si ya no hay llamadas a tools,
        # significa que tenemos la respuesta final.
        if not function_calls:
            break

        tool_outputs = []

        for call in function_calls:
            nombre = call.name

            argumentos = json.loads(
                call.arguments or "{}"
            )

            # Ejecutar únicamente tools permitidas
            # para clientes.
            resultado = ejecutar_cliente_tool(
                nombre,
                argumentos,
                user_id=user_id
            )

            tools_utilizadas.append(nombre)

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(
                    resultado,
                    ensure_ascii=False,
                    default=str
                )
            })

        # Enviar los resultados de las tools
        # nuevamente al modelo.
        response = continuar_respuesta(
            response_id=response.id,
            tool_outputs=tool_outputs,
            instrucciones=instrucciones,
            tools=CLIENTE_TOOLS
        )

    # Obtener respuesta final
    respuesta = response.output_text.strip()

    if not respuesta:
        respuesta = (
            "No pude obtener una respuesta en este momento. "
            "Inténtalo nuevamente."
        )

    # Guardamos el turno completo solamente
    # después de obtener la respuesta.
    guardar_turno_cliente(
        user_id,
        conversation_id,
        mensaje,
        respuesta
    )

    return {
        "respuesta": respuesta,
        "tools_utilizadas": tools_utilizadas,
        "grafica": None,
        "conversation_id": conversation_id
    }
