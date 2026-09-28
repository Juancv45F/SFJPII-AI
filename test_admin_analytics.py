import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch
from bson import ObjectId

from tools import inventario, ventas, pedidos, cliente_pedidos
from services import admin_tools, cliente_tools
from services.chart_service import crear_grafica
from prompts.admin import obtener_admin_prompt
from prompts.cliente import obtener_cliente_prompt
from database import client as mongo_client


def tearDownModule():
    mongo_client.close()


INICIO = datetime(2026, 9, 1, tzinfo=timezone.utc)
FIN = datetime(2026, 9, 30, 23, 59, 59, tzinfo=timezone.utc)


class AdminAnalyticsTest(unittest.TestCase):
    def test_cliente_tools_inyectan_usuario_fuera_del_esquema_de_la_ia(self):
        for tool in cliente_tools.CLIENTE_TOOLS:
            self.assertNotIn("user_id", tool["parameters"].get("properties", {}))

        user_id = str(ObjectId())
        cursor = Mock()
        cursor.sort.return_value.limit.return_value = []
        fake = SimpleNamespace(pedidos=Mock(), encargos=Mock())
        fake.pedidos.find.return_value = cursor
        with patch.object(cliente_pedidos, "db", fake):
            resultado = cliente_tools.ejecutar_cliente_tool(
                "consultar_mis_pedidos", {"limite": 5}, user_id=user_id
            )
        self.assertEqual(resultado, [])
        self.assertEqual(fake.pedidos.find.call_args.args[0], {"userId": ObjectId(user_id)})

    def test_detalle_de_pedido_siempre_se_limita_al_propietario(self):
        user_id = str(ObjectId())
        pedido_id = str(ObjectId())
        fake = SimpleNamespace(pedidos=Mock())
        fake.pedidos.find_one.return_value = None
        with patch.object(cliente_pedidos, "db", fake):
            resultado = cliente_pedidos.consultar_mi_pedido(user_id, pedido_id)
        self.assertFalse(resultado["encontrado"])
        self.assertEqual(fake.pedidos.find_one.call_args.args[0], {
            "_id": ObjectId(pedido_id), "userId": ObjectId(user_id)
        })

    def test_pedidos_y_encargos_validan_estado_e_identificadores(self):
        with self.assertRaises(ValueError):
            cliente_pedidos.consultar_mi_pedido(str(ObjectId()), "pedido-invalido")
        with self.assertRaises(ValueError):
            cliente_pedidos.consultar_mis_pedidos(str(ObjectId()), "desconocido")
        prompt = obtener_cliente_prompt()
        self.assertIn("Nunca pidas", prompt)
        self.assertIn("consultar_mis_encargos", prompt)

    def test_prioriza_agotados_con_ventas_y_excluye_solo_encargo(self):
        fake = SimpleNamespace(pedidos=Mock(), productos=Mock())
        fake.pedidos.aggregate.return_value = [
            {"_id": "agotado", "cantidad_vendida": 20, "ingresos": 500},
            {"_id": "bajo", "cantidad_vendida": 8, "ingresos": 160}
        ]
        fake.productos.find.return_value = [
            {"_id": "bajo", "nombre": "B", "stock": 3, "categoria": {"nombre": "Farmacia"}},
            {"_id": "agotado", "nombre": "A", "stock": 0, "categoria": {"nombre": "Farmacia"}},
            {"_id": "sin-ventas", "nombre": "C", "stock": 1}
        ]
        with patch.object(inventario, "db", fake):
            resultado = inventario.reabastecimiento_priorizado(INICIO, FIN, 10, 10)
        self.assertEqual([x["producto_id"] for x in resultado], ["agotado", "bajo", "sin-ventas"])
        self.assertEqual(resultado[0]["prioridad"], "urgente")
        self.assertEqual(fake.productos.find.call_args.args[0]["solo_encargo"], {"$ne": True})

    def test_todas_las_consultas_de_inventario_fisico_excluyen_solo_encargo(self):
        cursor = Mock()
        cursor.sort.return_value = []
        fake_inventory = SimpleNamespace(productos=Mock())
        fake_inventory.productos.find.return_value = cursor
        fake_inventory.productos.count_documents.side_effect = [3, 1, 1, 1, 2]
        with patch.object(inventario, "db", fake_inventory):
            inventario.productos_stock_bajo(10)
            resumen = inventario.analizar_inventario(10)
        self.assertEqual(fake_inventory.productos.find.call_args.args[0]["solo_encargo"], {"$ne": True})
        self.assertTrue(all(call.args[0].get("solo_encargo") == {"$ne": True}
                            for call in fake_inventory.productos.count_documents.call_args_list[:4]))
        self.assertEqual(resumen["productos_solo_encargo_excluidos"], 2)

        fake_sales = SimpleNamespace(pedidos=Mock(), productos=Mock())
        fake_sales.pedidos.aggregate.return_value = []
        fake_sales.productos.find.return_value = []
        with patch.object(ventas, "db", fake_sales):
            self.assertEqual(ventas.productos_baja_rotacion(INICIO, FIN), [])
            self.assertEqual(ventas.analizar_oportunidades_oferta(INICIO, FIN), [])
        for call in fake_sales.productos.find.call_args_list:
            self.assertEqual(call.args[0]["solo_encargo"], {"$ne": True})

    def test_productos_vendidos_incluyen_ingresos_stock_y_estado_catalogo(self):
        fake = SimpleNamespace(pedidos=Mock(), productos=Mock())
        fake.pedidos.aggregate.return_value = [
            {"_productoId": "uno", "productoId": "uno", "nombre": "Uno", "cantidad_vendida": 7, "ingresos": 210},
            {"_productoId": "retirado", "productoId": "retirado", "nombre": "Viejo", "cantidad_vendida": 4, "ingresos": 80}
        ]
        fake.productos.find.return_value = [{"_id": "uno", "stock": 2, "categoria": {"nombre": "Bebés"}}]
        with patch.object(ventas, "db", fake):
            resultado = ventas.productos_mas_vendidos(INICIO, FIN, 10, "ingresos")
        self.assertEqual(resultado[0]["stock_actual"], 2)
        self.assertTrue(resultado[0]["en_catalogo"])
        self.assertFalse(resultado[1]["en_catalogo"])
        self.assertIsNone(resultado[1]["stock_actual"])
        self.assertEqual(fake.productos.find.call_args.args[0], {"_id": {"$in": ["uno", "retirado"]}})
        sort_stage = next(x["$sort"] for x in fake.pedidos.aggregate.call_args.args[0] if "$sort" in x)
        self.assertEqual(sort_stage, {"ingresos": -1})

    def test_ingresos_por_categoria_usan_lookup_y_ventas_por_dia_zona_local(self):
        fake = SimpleNamespace(pedidos=Mock())
        fake.pedidos.aggregate.side_effect = [
            [{"categoria": "Farmacia", "ingresos": 100, "unidades_vendidas": 3}],
            [{"fecha": "2026-09-10", "ingresos": 100, "pedidos": 2}]
        ]
        with patch.object(ventas, "db", fake):
            ventas.ingresos_por_categoria(INICIO, FIN)
            ventas.ventas_por_dia(INICIO, FIN)
        categoria_pipeline = fake.pedidos.aggregate.call_args_list[0].args[0]
        dia_pipeline = fake.pedidos.aggregate.call_args_list[1].args[0]
        self.assertTrue(any("$lookup" in stage for stage in categoria_pipeline))
        self.assertIn("Fuera del catálogo / sin categoría", str(categoria_pipeline))
        self.assertIn("America/Mexico_City", str(dia_pipeline))

    def test_resumen_pedidos_calcula_ticket_y_estados(self):
        fake = SimpleNamespace(pedidos=Mock())
        fake.pedidos.aggregate.side_effect = [
            [{"estado": "entregado", "cantidad": 2}, {"estado": "cancelado", "cantidad": 1}],
            [{"total_pedidos": 3, "pedidos_completados": 2, "pedidos_cancelados": 1,
              "pedidos_con_ingreso": 2, "ingresos": 350}]
        ]
        with patch.object(pedidos, "db", fake):
            resultado = pedidos.analizar_pedidos(INICIO, FIN)
        self.assertEqual(resultado["ticket_promedio"], 175)
        self.assertEqual(resultado["por_estado"][1]["estado"], "cancelado")
        resumen_pipeline = fake.pedidos.aggregate.call_args_list[1].args[0]
        self.assertNotIn("cancelado", str(next(stage for stage in resumen_pipeline if "$group" in stage)["$group"]["ingresos"]))

    def test_encargos_se_mantienen_separados_de_pedidos(self):
        fake = SimpleNamespace(encargos=Mock())
        fake.encargos.aggregate.return_value = [{
            "estados": [{"_id": "pendiente", "cantidad": 4}],
            "entregas": [{"_id": "recoger", "cantidad": 3}],
            "totales": [{"total_encargos": 4, "total_estimado": 925.5}]
        }]
        with patch.object(pedidos, "db", fake):
            resultado = pedidos.analizar_encargos(INICIO, FIN)
        self.assertEqual(resultado["total_encargos"], 4)
        self.assertEqual(resultado["por_tipo_entrega"][0]["tipo_entrega"], "recoger")

    def test_nuevas_consultas_generan_graficas_compatibles(self):
        casos = {
            "reabastecimiento_priorizado": ([{"nombre": "A", "cantidad_vendida": 8}], "bar"),
            "ingresos_por_categoria": ([{"categoria": "Farmacia", "ingresos": 500}], "bar"),
            "ventas_por_dia": ([{"fecha": "2026-09-01", "ingresos": 250}], "bar"),
            "analizar_pedidos": ({"por_estado": [{"estado": "entregado", "cantidad": 2}]}, "doughnut"),
            "evolucion_pedidos": ([{"fecha": "2026-09-01", "pedidos": 4}], "bar"),
            "analizar_encargos": ({"por_estado": [{"estado": "pendiente", "cantidad": 3}]}, "doughnut")
        }
        for nombre, (datos, tipo) in casos.items():
            with self.subTest(nombre=nombre):
                grafica = crear_grafica(nombre, datos)
                self.assertEqual(grafica["tipo"], tipo)
                self.assertEqual(len(grafica["labels"]), len(grafica["data"]))
                self.assertIn("unidad", grafica)

    def test_registro_de_tools_es_estricto_y_ejecutor_valida_periodos(self):
        nombres = [tool["name"] for tool in admin_tools.ADMIN_TOOLS]
        for nombre in ["reabastecimiento_priorizado", "ingresos_por_categoria", "ventas_por_dia",
                       "analizar_pedidos", "evolucion_pedidos", "analizar_encargos"]:
            self.assertIn(nombre, nombres)
        for tool in admin_tools.ADMIN_TOOLS:
            if tool.get("strict"):
                self.assertEqual(set(tool["parameters"]["properties"]), set(tool["parameters"]["required"]))
        with self.assertRaises(ValueError):
            admin_tools.ejecutar_tool("ventas_por_dia", {"fecha_inicio": FIN.isoformat(), "fecha_fin": INICIO.isoformat()})
        with self.assertRaises(ValueError):
            admin_tools.ejecutar_tool("productos_stock_bajo", {"limite": -1})
        with self.assertRaises(ValueError):
            admin_tools.ejecutar_tool("ventas_totales", {"fecha_inicio": "no-es-fecha", "fecha_fin": FIN.isoformat()})

    def test_prompt_guia_seguimientos_y_no_contabiliza_cancelados(self):
        prompt = obtener_admin_prompt()
        self.assertIn('"de esos"', prompt)
        self.assertIn("pedidos pendientes o cancelados", prompt)
        self.assertIn("vuelve a ejecutar", prompt.lower())


if __name__ == "__main__":
    unittest.main()
