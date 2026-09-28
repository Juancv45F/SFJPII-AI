import sys
import types
import unittest
from unittest.mock import Mock
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Aislamos credenciales, MongoDB y consumo de IA en estas pruebas de contrato.
settings = types.SimpleNamespace(sfjpii_ai_service_key="test-key")
sys.modules['config'] = types.SimpleNamespace(settings=settings)
agent = Mock(return_value={"respuesta": "Resultado", "tools_utilizadas": [], "grafica": None})
sys.modules['agents.admin_agent'] = types.SimpleNamespace(procesar_mensaje_admin=agent)
from security import require_service_key
from routes.admin import router
app = FastAPI()
app.include_router(router, dependencies=[Depends(require_service_key)])
client = TestClient(app)

class AdminIntegrationTest(unittest.TestCase):
    def setUp(self):
        settings.sfjpii_ai_service_key = 'test-key'
        agent.reset_mock()
        agent.side_effect = None

    def test_authentication(self):
        for headers in ({}, {'X-Service-Key': 'wrong'}):
            self.assertEqual(client.post('/admin/chat', json={'mensaje': 'ventas'}, headers=headers).status_code, 401)
        agent.assert_not_called()

    def test_missing_configuration(self):
        settings.sfjpii_ai_service_key = ''
        self.assertEqual(client.post('/admin/chat', json={'mensaje': 'ventas'}).status_code, 503)

    def test_response_contract(self):
        response = client.post('/admin/chat', json={'mensaje': 'ventas'}, headers={'X-Service-Key': 'test-key'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['respuesta'], 'Resultado')
        agent.assert_called_once_with('ventas')

    def test_errors_do_not_expose_credentials(self):
        agent.side_effect = RuntimeError('secret')
        response = client.post('/admin/chat', json={'mensaje': 'ventas'}, headers={'X-Service-Key': 'test-key'})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('secret', response.text)

if __name__ == '__main__':
    unittest.main()
