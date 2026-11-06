import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from openai import APITimeoutError

fake_settings = SimpleNamespace(ai_provider="deepseek", ai_model="modelo-prueba",
                                ai_base_url="https://example.test", ai_api_key="test-key",
                                ai_reasoning_effort="none", ai_request_timeout_seconds=45,
                                ai_turn_timeout_seconds=225, ai_max_output_tokens=2048)
original_config = sys.modules.get("config")
sys.modules["config"] = types.SimpleNamespace(settings=fake_settings)
try:
    from services import llm_service
finally:
    if original_config is None:
        sys.modules.pop("config", None)
    else:
        sys.modules["config"] = original_config

TOOLS = [{"type": "function", "name": "buscar_producto", "description": "Busca",
          "parameters": {"type": "object", "properties": {}}, "strict": True}]


def completion(content=None, tool_calls=None):
    return SimpleNamespace(id="chat-1", choices=[SimpleNamespace(
        message=SimpleNamespace(content=content, tool_calls=tool_calls))])


class LlmServiceTests(unittest.TestCase):
    def setUp(self):
        fake_settings.ai_provider = "deepseek"
        fake_settings.ai_reasoning_effort = "none"
        fake_settings.ai_turn_timeout_seconds = 225
        self.create = Mock()
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=self.create)))
        patcher = patch.object(llm_service, "client", fake_client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_tool_round_trip_keeps_conversation_and_contract(self):
        llamada = SimpleNamespace(id="call-1", function=SimpleNamespace(name="buscar_producto", arguments='{"nombre": "x"}'))
        self.create.side_effect = [completion(tool_calls=[llamada]), completion(content="Listo")]

        primera = llm_service.crear_respuesta("hola", [{"role": "assistant", "content": "antes"}], "reglas", TOOLS)
        self.assertEqual(primera.output_text, "")
        self.assertEqual((primera.output[0].type, primera.output[0].name, primera.output[0].call_id),
                         ("function_call", "buscar_producto", "call-1"))

        kwargs = self.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "modelo-prueba")
        self.assertEqual(kwargs["messages"][0], {"role": "system", "content": "reglas"})
        self.assertEqual(kwargs["messages"][-1], {"role": "user", "content": "hola"})
        self.assertEqual(kwargs["tools"], [{"type": "function", "function": {
            "name": "buscar_producto", "description": "Busca", "parameters": TOOLS[0]["parameters"]}}])
        self.assertEqual(kwargs["extra_body"], {"thinking": {"type": "disabled"}})

        final = llm_service.continuar_respuesta(
            primera, [{"type": "function_call_output", "call_id": "call-1", "output": "[]"}], "reglas", TOOLS)
        self.assertEqual(final.output, [])
        self.assertEqual(final.output_text, "Listo")

        mensajes = self.create.call_args.kwargs["messages"]
        self.assertEqual([m["role"] for m in mensajes], ["system", "assistant", "user", "assistant", "tool"])
        self.assertEqual(mensajes[3]["tool_calls"][0]["id"], "call-1")
        self.assertEqual(mensajes[4], {"role": "tool", "tool_call_id": "call-1", "content": "[]"})

    def test_qwen_does_not_receive_deepseek_options(self):
        fake_settings.ai_provider = "qwen"
        self.create.return_value = completion(content="Hola")

        llm_service.crear_respuesta("hola", [], "reglas", TOOLS)

        self.assertNotIn("extra_body", self.create.call_args.kwargs)
        self.assertNotIn("reasoning_effort", self.create.call_args.kwargs)

    def test_deepseek_does_not_receive_reasoning_effort(self):
        self.create.return_value = completion(content="Hola")

        llm_service.crear_respuesta("hola", [], "reglas", TOOLS)

        self.assertNotIn("reasoning_effort", self.create.call_args.kwargs)

    def test_openai_disables_reasoning_for_tools_without_deepseek_options(self):
        fake_settings.ai_provider = "openai"
        llamada = SimpleNamespace(id="call-1", function=SimpleNamespace(name="buscar_producto", arguments="{}"))
        self.create.side_effect = [completion(tool_calls=[llamada]), completion(content="Listo")]

        primera = llm_service.crear_respuesta("hola", [], "reglas", TOOLS)
        llm_service.continuar_respuesta(
            primera, [{"type": "function_call_output", "call_id": "call-1", "output": "[]"}], "reglas", TOOLS)

        for llamada_api in self.create.call_args_list:
            self.assertEqual(llamada_api.kwargs["reasoning_effort"], "none")
            self.assertNotIn("extra_body", llamada_api.kwargs)
            self.assertNotIn("strict", llamada_api.kwargs["tools"][0]["function"])

    def test_openai_can_omit_reasoning_effort(self):
        fake_settings.ai_provider = "openai"
        fake_settings.ai_reasoning_effort = "off"
        self.create.return_value = completion(content="Hola")

        llm_service.crear_respuesta("hola", [], "reglas", TOOLS)

        self.assertNotIn("reasoning_effort", self.create.call_args.kwargs)

    def test_every_provider_call_caps_generated_tokens(self):
        self.create.return_value = completion(content="Hola")
        esperado = {"deepseek": "max_tokens", "qwen": "max_tokens", "openai": "max_completion_tokens"}

        for proveedor, parametro in esperado.items():
            fake_settings.ai_provider = proveedor
            llm_service.crear_respuesta("hola", [], "reglas", TOOLS)
            kwargs = self.create.call_args.kwargs
            self.assertEqual(kwargs[parametro], 2048)
            otro = "max_tokens" if parametro == "max_completion_tokens" else "max_completion_tokens"
            self.assertNotIn(otro, kwargs)

    def test_each_call_timeout_is_capped_by_the_remaining_turn_budget(self):
        self.create.return_value = completion(content="Hola")

        llm_service.crear_respuesta("hola", [], "reglas", TOOLS)
        self.assertEqual(self.create.call_args.kwargs["timeout"], 45)

        fake_settings.ai_turn_timeout_seconds = 10
        llm_service.crear_respuesta("hola", [], "reglas", TOOLS)
        self.assertLessEqual(self.create.call_args.kwargs["timeout"], 10)

    def test_expired_turn_stops_before_calling_the_model_again(self):
        self.create.return_value = completion(content="Hola")
        primera = llm_service.crear_respuesta("hola", [], "reglas", TOOLS)
        primera.limite = 0
        self.create.reset_mock()

        with self.assertRaises(APITimeoutError):
            llm_service.continuar_respuesta(primera, [], "reglas", TOOLS)

        self.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
