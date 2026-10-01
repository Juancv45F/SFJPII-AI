import unittest

from services.client_scope import es_consulta_permitida


class ClientScopeTest(unittest.TestCase):
    def test_rejects_math_and_general_internet_questions(self):
        self.assertFalse(es_consulta_permitida("¿Cuánto es 25 por 8?"))
        self.assertFalse(es_consulta_permitida("¿Qué navegador de internet me recomiendas?"))
        self.assertFalse(es_consulta_permitida("Escribe un programa en Python"))

    def test_accepts_pharmacy_questions(self):
        self.assertTrue(es_consulta_permitida("¿Tienen atorvastatina?"))
        self.assertTrue(es_consulta_permitida("¿Cuál es el horario de la farmacia?"))
        self.assertTrue(es_consulta_permitida("Muéstrame mis encargos"))

    def test_accepts_a_short_follow_up_only_with_history(self):
        history = [{"role": "assistant", "content": "Hay dos productos."}]
        self.assertTrue(es_consulta_permitida("¿Y el segundo?", history))
        self.assertFalse(es_consulta_permitida("¿Y el segundo?"))

if __name__ == "__main__":
    unittest.main()
