import json
import importlib.util
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

dependency_names = ["services.llm_service", "services.conversation_service"]
original_dependencies = {name: sys.modules.get(name) for name in dependency_names}
sys.modules["services.llm_service"] = SimpleNamespace(crear_respuesta_admin=lambda **_: None,
                                                        continuar_respuesta_admin=lambda **_: None)
sys.modules["services.conversation_service"] = SimpleNamespace(obtener_historial=lambda *_: [],
                                                                 guardar_turno=lambda *_args, **_kwargs: None)
try:
    spec = importlib.util.spec_from_file_location("stress_admin_agent", Path(__file__).parent / "agents" / "admin_agent.py")
    admin_agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(admin_agent)
finally:
    for dependency, original in original_dependencies.items():
        if original is None:
            sys.modules.pop(dependency, None)
        else:
            sys.modules[dependency] = original


class ConversationStressTest(unittest.TestCase):
    def test_six_dependent_questions_keep_context_and_chart_contract(self):
        turns = [
            ("¿Cuáles fueron mis productos más vendidos este mes?", "productos_mas_vendidos"),
            ("¿Cuáles de esos tienen poco stock?", "reabastecimiento_priorizado"),
            ("¿Cuánto dinero generaron?", "productos_mas_vendidos"),
            ("Compara eso con el mes anterior.", "comparar_ventas"),
            ("Hazme una gráfica.", "productos_mas_vendidos"),
            ("¿Cuál de esos ya no está en el catálogo?", "productos_mas_vendidos")
        ]
        history = []
        observed_histories = []
        active = {"index": 0}

        def create_response(mensaje, historial, instrucciones, tools):
            index = active["index"]
            observed_histories.append(list(historial))
            name = turns[index][1]
            arguments = {"fecha_inicio": "2026-09-01T00:00:00+00:00", "fecha_fin": "2026-09-30T23:59:59+00:00"}
            if name == "productos_mas_vendidos":
                arguments.update({"limite": 10, "metrica": "ingresos" if index == 2 else "cantidad"})
            elif name == "reabastecimiento_priorizado":
                arguments.update({"limite_stock": 10, "limite": 10})
            elif name == "comparar_ventas":
                arguments = {"periodo1_inicio": "2026-09-01T00:00:00+00:00", "periodo1_fin": "2026-09-30T23:59:59+00:00",
                             "periodo2_inicio": "2026-08-01T00:00:00+00:00", "periodo2_fin": "2026-08-31T23:59:59+00:00"}
            return SimpleNamespace(id=f"response-{index}", output=[SimpleNamespace(
                type="function_call", name=name, arguments=json.dumps(arguments), call_id=f"call-{index}")])

        def continue_response(response_id, tool_outputs, instrucciones, tools):
            return SimpleNamespace(id=response_id, output=[], output_text=f"Respuesta administrativa {active['index'] + 1}")

        def save_turn(admin_id, conversation_id, mensaje, respuesta, grafica=None):
            history.extend([{"role": "user", "content": mensaje}, {"role": "assistant", "content": respuesta}])

        tool_result = [{"nombre": "Producto A", "cantidad_vendida": 8, "ingresos": 400,
                        "stock_actual": 2, "en_catalogo": True, "metrica_orden": "cantidad"}]
        chart = {"tipo": "bar", "titulo": "Productos más vendidos", "labels": ["Producto A"], "data": [8]}

        with patch.object(admin_agent, "obtener_historial", side_effect=lambda *_: list(history)), \
             patch.object(admin_agent, "crear_respuesta_admin", side_effect=create_response), \
             patch.object(admin_agent, "continuar_respuesta_admin", side_effect=continue_response), \
             patch.object(admin_agent, "ejecutar_tool", return_value=tool_result), \
             patch.object(admin_agent, "crear_grafica", return_value=chart), \
             patch.object(admin_agent, "guardar_turno", side_effect=save_turn):
            responses = []
            for index, (question, _) in enumerate(turns):
                active["index"] = index
                responses.append(admin_agent.procesar_mensaje_admin(question, "conversation-1", "admin-1"))

        self.assertEqual([len(items) for items in observed_histories], [0, 2, 4, 6, 8, 10])
        self.assertTrue(all(response["conversation_id"] == "conversation-1" for response in responses))
        self.assertIsNone(responses[0]["grafica"])
        self.assertEqual(responses[4]["grafica"], chart)
        self.assertIsNone(responses[5]["grafica"])
        self.assertEqual(len(history), 12)


if __name__ == "__main__":
    unittest.main()
