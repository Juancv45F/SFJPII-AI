import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tools.validators import ToolValidationError

# tools.productos importa database; se aísla para no depender de configuración real.
with patch.dict(sys.modules, {"database": SimpleNamespace(db=MagicMock())}):
    sys.modules.pop("tools.productos", None)
    from tools import productos

RAIZ = Path(__file__).resolve().parent

# Corre en un proceso aparte con variables dummy y fuera del repo: no carga .env
# ni los módulos simulados por otras pruebas. Ninguna ruta llega a MongoDB porque
# la clave se rechaza antes; solo /health/deep con clave válida lo intenta, contra
# un puerto cerrado.
SONDA_RUTAS = """
import json
from unittest.mock import patch
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)
rutas = {}
for ruta, metodos in main.app.openapi()["paths"].items():
    if ruta in ("/", "/health"):
        continue
    url = ruta.replace("{conversation_id}", "chat-1")
    for metodo in metodos:
        rutas[f"{metodo} {ruta}"] = [
            client.request(metodo, url, headers=headers, json={"mensaje": "hola"}).status_code
            for headers in ({}, {"X-Service-Key": ""}, {"X-Service-Key": "incorrecta"})
        ]
clave = {"X-Service-Key": "clave-de-prueba"}
with patch.object(main, "verificar_conexion") as ping:
    publico = client.get("/health")
    publico_toca_mongo = ping.called
    profundo_ok = client.get("/health/deep", headers=clave)
profundo_caido = client.get("/health/deep", headers=clave)
print(json.dumps({
    "rutas": rutas,
    "salud": {
        "publico": [publico.status_code, publico.json()],
        "publico_sin_mongo": client.get("/health").status_code,
        "publico_toca_mongo": publico_toca_mongo,
        "profundo_ok": [profundo_ok.status_code, profundo_ok.json()],
        "profundo_caido": profundo_caido.status_code,
    },
    "documentacion": {ruta: client.get(ruta).status_code for ruta in ("/docs", "/redoc", "/openapi.json")},
}))
"""


def ejecutar_sonda():
    entorno = {
        **{k: v for k, v in os.environ.items() if k.upper() in {"PATH", "SYSTEMROOT", "TEMP", "TMP"}},
        "PYTHONPATH": str(RAIZ),
        "PYTHONDONTWRITEBYTECODE": "1",
        "MONGODB_URI": "mongodb://127.0.0.1:1/?serverSelectionTimeoutMS=200",
        "MONGODB_DATABASE": "dummy",
        "SFJPII_AI_SERVICE_KEY": "clave-de-prueba",
        "AI_PROVIDER": "deepseek",
        "DEEPSEEK_API_KEY": "dummy",
        "AI_BASE_URL": "http://127.0.0.1:1",
    }
    with tempfile.TemporaryDirectory() as directorio:
        salida = subprocess.run([sys.executable, "-c", SONDA_RUTAS], cwd=directorio, env=entorno,
                                capture_output=True, text=True, encoding="utf-8", timeout=60)
    if salida.returncode:
        raise AssertionError(salida.stderr[-2000:])
    return json.loads(salida.stdout.strip().splitlines()[-1])


class SuperficiePublicaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultado = ejecutar_sonda()

    def test_documentacion_no_es_publica(self):
        self.assertEqual(set(self.resultado["documentacion"].values()), {404})

    def test_toda_ruta_de_negocio_exige_la_clave(self):
        protegidas = self.resultado["rutas"]
        self.assertGreater(len(protegidas), 15)
        for ruta, estados in protegidas.items():
            self.assertEqual(estados, [401, 401, 401], ruta)
        self.assertIn("get /health/deep", protegidas)

    def test_health_publico_no_expone_ni_toca_mongo(self):
        salud = self.resultado["salud"]
        self.assertEqual(salud["publico"], [200, {"status": "ok"}])
        self.assertEqual(salud["publico_sin_mongo"], 200)
        self.assertFalse(salud["publico_toca_mongo"])

    def test_health_deep_refleja_el_estado_de_mongo(self):
        salud = self.resultado["salud"]
        self.assertEqual(salud["profundo_ok"], [200, {"status": "ok", "mongodb": "connected"}])
        self.assertEqual(salud["profundo_caido"], 503)


class BusquedaProductosTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.productos.find_one.return_value = None
        self.db.productos.find.return_value.limit.return_value = []
        patcher = patch.object(productos, "db", self.db)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_el_texto_se_busca_literal_y_no_como_regex(self):
        ataque = "(a+)+$"
        productos.buscar_producto(ataque)
        self.assertEqual(self.db.productos.find_one.call_args.args[0]["nombre"]["$regex"], r"\(a\+\)\+\$")

        productos.productos_por_categoria(".*|x")
        self.assertEqual(self.db.productos.find.call_args.args[0]["categoria.nombre"]["$regex"], r"^\.\*\|x$")

        productos.buscar_productos(ataque)
        for condicion in self.db.productos.find.call_args.args[0]["$or"]:
            self.assertEqual(next(iter(condicion.values()))["$regex"], r"\(a\+\)\+\$")

    def test_argumentos_del_modelo_invalidos_no_llegan_a_mongo(self):
        for valor in ({"$ne": ""}, ["x"], 1, None, "", "   ", "x" * 101):
            for funcion in (productos.buscar_producto, productos.productos_por_categoria, productos.buscar_productos):
                with self.subTest(funcion=funcion.__name__, valor=valor), self.assertRaises(ToolValidationError):
                    funcion(valor)
        self.db.productos.find_one.assert_not_called()
        self.db.productos.find.assert_not_called()

    def test_busqueda_normal_sigue_funcionando(self):
        resultado = productos.buscar_producto(" Paracetamol ")
        self.assertFalse(resultado["encontrado"])
        self.assertEqual(resultado["nombre_buscado"], "Paracetamol")


if __name__ == "__main__":
    unittest.main()
