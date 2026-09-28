import json

from services.llm_service import (
    crear_respuesta_admin,
    continuar_respuesta_admin
)

from services.conversation_service import (
    obtener_historial,
    agregar_mensaje
)


from services.admin_tools import (
    ADMIN_TOOLS,
    ejecutar_tool,
    serializar_resultado
)

from services.chart_service import crear_grafica
from prompts.admin import obtener_admin_prompt

def procesar_mensaje_admin(
    mensaje: str,
    conversation_id: str
):
    historial = obtener_historial(
        conversation_id
    )

    agregar_mensaje(
        conversation_id,
        "user",
        mensaje
    )

   
    instrucciones = obtener_admin_prompt()

    response = crear_respuesta_admin(
        mensaje=mensaje,
        historial=historial,
        instrucciones=instrucciones,
        tools=ADMIN_TOOLS
    )

    tools_utilizadas = []

    resultados_tools = []

    for _ in range(5):

        llamadas = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # Ya tenemos la respuesta final
        if not llamadas:

            grafica = None

            # Solo generamos gráfica si el usuario
            # realmente la pidió.
            solicita_grafica = any(
                palabra in mensaje.lower()
                for palabra in [
                    "gráfica",
                    "grafica",
                    "gráfico",
                    "grafico"
                ]
            )

            if solicita_grafica:

                for resultado_tool in resultados_tools:

                    posible_grafica = crear_grafica(
                        resultado_tool["tool"],
                        resultado_tool["resultado"]
                    )

                    if posible_grafica:
                        grafica = posible_grafica
                        break

            agregar_mensaje(
                conversation_id,
                "assistant",
                response.output_text
            )

            return {
                "respuesta": response.output_text,
                "tools_utilizadas": tools_utilizadas,
                "grafica": grafica,
                "conversation_id": conversation_id
            }

        tool_outputs = []

        for llamada in llamadas:

            argumentos = json.loads(
                llamada.arguments
            )

            resultado = ejecutar_tool(
                llamada.name,
                argumentos
            )

            # Guardamos qué herramienta utilizó.
            tools_utilizadas.append(
                llamada.name
            )

            # Guardamos los datos reales obtenidos
            # de MongoDB.
            resultados_tools.append(
                {
                    "tool": llamada.name,
                    "resultado": resultado
                }
            )

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": llamada.call_id,
                    "output": serializar_resultado(
                        resultado
                    )
                }
            )

        response = continuar_respuesta_admin(
            response_id=response.id,
            tool_outputs=tool_outputs,
            instrucciones=instrucciones,
            tools=ADMIN_TOOLS
        )

    return {
        "respuesta": (
            "No pude completar el análisis "
            "después de varias consultas."
        ),
        "tools_utilizadas": tools_utilizadas,
        "grafica": None
    }