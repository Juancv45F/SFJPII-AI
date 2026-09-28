import sys
import types
import unittest
from unittest.mock import Mock
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Aislamos credenciales, MongoDB y consumo de IA en estas pruebas de contrato.
settings = types.SimpleNamespace(sfjpii_ai_service_key="test-key", chat_retention_days=180)
sys.modules['config'] = types.SimpleNamespace(settings=settings)
collection = Mock()
sys.modules['database'] = types.SimpleNamespace(db=types.SimpleNamespace(conversaciones_ai=collection))
agent = Mock(return_value={"respuesta": "Resultado", "tools_utilizadas": [], "grafica": None, "conversation_id": "test-chat"})
sys.modules['agents.admin_agent'] = types.SimpleNamespace(procesar_mensaje_admin=agent)
client_agent = Mock(return_value={"respuesta": "Tu pedido está pendiente", "tools_utilizadas": ["consultar_mis_pedidos"], "grafica": None, "conversation_id": "client-chat"})
sys.modules['agents.cliente_agent'] = types.SimpleNamespace(procesar_mensaje_cliente=client_agent)
from security import require_service_key
from routes.admin import router as admin_router
from routes.cliente import router as client_router
from tools.validators import ToolValidationError
app = FastAPI()
app.include_router(admin_router, dependencies=[Depends(require_service_key)])
app.include_router(client_router, dependencies=[Depends(require_service_key)])
client = TestClient(app)

class AdminIntegrationTest(unittest.TestCase):
    def setUp(self):
        settings.sfjpii_ai_service_key = 'test-key'
        agent.reset_mock()
        agent.side_effect = None
        client_agent.reset_mock()
        client_agent.side_effect = None

    def test_authentication(self):
        for headers in ({}, {'X-Service-Key': 'wrong'}):
            self.assertEqual(client.post('/admin/chat', json={'mensaje': 'ventas'}, headers=headers).status_code, 401)
        agent.assert_not_called()

    def test_missing_configuration(self):
        settings.sfjpii_ai_service_key = ''
        self.assertEqual(client.post('/admin/chat', json={'mensaje': 'ventas'}).status_code, 503)

    def test_response_contract(self):
        response = client.post('/admin/chat', json={'mensaje': 'ventas', 'conversation_id': 'test-chat'}, headers={'X-Service-Key': 'test-key', 'X-Admin-Id': 'owner'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['respuesta'], 'Resultado')
        agent.assert_called_once_with(mensaje='ventas', conversation_id='test-chat', admin_id='owner')

    def test_errors_do_not_expose_credentials(self):
        agent.side_effect = RuntimeError('secret')
        response = client.post('/admin/chat', json={'mensaje': 'ventas'}, headers={'X-Service-Key': 'test-key', 'X-Admin-Id': 'owner'})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('secret', response.text)

    def test_invalid_tool_arguments_return_422(self):
        agent.side_effect = ToolValidationError('fecha_inicio debe ser una fecha ISO 8601 válida')
        response = client.post('/admin/chat', json={'mensaje': 'ventas'}, headers={'X-Service-Key': 'test-key', 'X-Admin-Id': 'owner'})
        self.assertEqual(response.status_code, 422)
        self.assertIn('fecha_inicio', response.json()['detail'])

    def test_history_is_scoped_to_admin(self):
        collection.find_one.return_value = None
        response = client.get('/admin/conversations/private', headers={'X-Service-Key': 'test-key', 'X-Admin-Id': 'owner'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(collection.find_one.call_args.args[0], {'admin_id': 'owner', 'conversation_id': 'private'})

    def test_two_admins_never_share_the_history_filter(self):
        collection.find_one.return_value = {'conversation_id': 'same', 'mensajes': []}
        for owner in ('admin-a', 'admin-b'):
            response = client.get('/admin/conversations/same', headers={'X-Service-Key': 'test-key', 'X-Admin-Id': owner})
            self.assertEqual(response.status_code, 200)
        filters = [call.args[0] for call in collection.find_one.call_args_list[-2:]]
        self.assertEqual(filters, [
            {'admin_id': 'admin-a', 'conversation_id': 'same'},
            {'admin_id': 'admin-b', 'conversation_id': 'same'}
        ])

    def test_list_has_titles_and_pagination(self):
        collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
            {'conversation_id': str(i), 'mensajes': [{'role': 'user', 'content': 'Ventas'}]} for i in range(31)]
        response = client.get('/admin/conversations', headers={'X-Service-Key': 'test-key', 'X-Admin-Id': 'owner'})
        self.assertEqual(len(response.json()['items']), 30)
        self.assertTrue(response.json()['has_more'])
        self.assertEqual(response.json()['items'][0]['titulo'], 'Ventas')
        self.assertEqual(collection.find.call_args.args[0], {'admin_id': 'owner'})

    def test_persists_complete_turn_with_chart_without_truncation(self):
        from services.conversation_service import guardar_turno
        chart = {'tipo': 'bar', 'titulo': 'Ventas', 'labels': ['A'], 'data': [5]}
        guardar_turno('owner', 'chat', 'Ventas', 'Resultado', chart)
        query, update = collection.update_one.call_args.args
        self.assertEqual(query, {'admin_id': 'owner', 'conversation_id': 'chat'})
        messages = update['$push']['mensajes']
        self.assertNotIn('$slice', messages)
        self.assertEqual(len(messages['$each']), 2)
        self.assertEqual(messages['$each'][1]['grafica'], chart)
        self.assertIn('expiresAt', update['$set'])

    def test_conversation_indexes_cover_owner_sort_and_retention(self):
        from services.conversation_service import preparar_indices_conversaciones
        collection.create_index.reset_mock()
        preparar_indices_conversaciones()
        self.assertEqual(collection.create_index.call_count, 5)
        self.assertTrue(collection.create_index.call_args_list[0].kwargs['unique'])
        self.assertEqual(collection.create_index.call_args_list[2].kwargs['expireAfterSeconds'], 0)
        self.assertTrue(collection.create_index.call_args_list[3].kwargs['unique'])

    def test_client_identity_comes_only_from_trusted_header(self):
        user_id = '507f1f77bcf86cd799439011'
        response = client.post('/cliente/chat', json={
            'mensaje': 'Mis pedidos', 'conversation_id': 'client-chat', 'user_id': 'otro'
        }, headers={'X-Service-Key': 'test-key', 'X-User-Id': user_id})
        self.assertEqual(response.status_code, 200)
        client_agent.assert_called_once_with(
            mensaje='Mis pedidos', conversation_id='client-chat', user_id=user_id
        )

    def test_client_rejects_invalid_trusted_identity(self):
        response = client.post('/cliente/chat', json={'mensaje': 'Mis pedidos'},
                               headers={'X-Service-Key': 'test-key', 'X-User-Id': 'otro'})
        self.assertEqual(response.status_code, 400)
        client_agent.assert_not_called()

    def test_two_clients_never_share_the_history_filter(self):
        from services.conversation_service import obtener_historial_cliente
        collection.find_one.return_value = None
        obtener_historial_cliente('client-a', 'same')
        obtener_historial_cliente('client-b', 'same')
        filters = [call.args[0] for call in collection.find_one.call_args_list[-2:]]
        self.assertEqual(filters, [
            {'tipo_usuario': 'cliente', 'user_id': 'client-a', 'conversation_id': 'same'},
            {'tipo_usuario': 'cliente', 'user_id': 'client-b', 'conversation_id': 'same'}
        ])

    def test_delete_is_scoped_to_admin(self):
        collection.delete_one.return_value.deleted_count = 1
        response = client.delete('/admin/conversations/private', headers={'X-Service-Key': 'test-key', 'X-Admin-Id': 'owner'})
        self.assertEqual(response.status_code, 204)
        collection.delete_one.assert_called_with({'admin_id': 'owner', 'conversation_id': 'private'})

    def test_delete_missing_or_foreign_conversation_returns_404(self):
        collection.delete_one.return_value.deleted_count = 0
        response = client.delete('/admin/conversations/private', headers={'X-Service-Key': 'test-key', 'X-Admin-Id': 'owner'})
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
