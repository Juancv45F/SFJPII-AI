import json
from datetime import datetime

from tools.productos import (
    buscar_producto,
    productos_con_descuento
)
from tools.inventario import productos_stock_bajo
from tools.ventas import (
    productos_mas_vendidos,
    ventas_totales,
    comparar_ventas,
    productos_baja_rotacion,
    analizar_oportunidades_oferta,
    ingresos_por_categoria,
    ventas_por_dia
)
from tools.pedidos import pedidos_por_estado, analizar_pedidos, evolucion_pedidos, analizar_encargos

from tools.ventas import comparar_ventas

from tools.inventario import (
    productos_para_reabastecer,
    analizar_inventario,
    reabastecimiento_priorizado
)


ADMIN_TOOLS = [
    {
    "type": "function",
    "name": "analizar_oportunidades_oferta",
    "description": (
        "Busca productos que podrían considerarse para una oferta "
        "o promoción basándose en baja rotación y stock disponible. "
        "No devuelve productos agotados. Úsala cuando el administrador "
        "pregunte qué productos podría poner en oferta o promoción."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "fecha_inicio": {
                "type": "string",
                "description": "Fecha inicial del periodo en ISO 8601."
            },
            "fecha_fin": {
                "type": "string",
                "description": "Fecha final del periodo en ISO 8601."
            },
            "limite_ventas": {
                "type": "integer",
                "description": (
                    "Máximo de unidades vendidas para considerar "
                    "un producto de baja rotación."
                )
            },
            "stock_minimo": {
                "type": "integer",
                "description": (
                    "Stock mínimo que debe tener un producto "
                    "para poder considerarlo para una promoción."
                )
            }
        },
        "required": [
            "fecha_inicio",
            "fecha_fin",
            "limite_ventas",
            "stock_minimo"
        ],
        "additionalProperties": False
    },
    "strict": True
},
    {
    "type": "function",
    "name": "productos_baja_rotacion",
    "description": (
        "Obtiene productos con pocas ventas durante un periodo. "
        "Úsala cuando el administrador pregunte qué productos "
        "se venden poco, tienen baja rotación o pocas ventas."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "fecha_inicio": {
                "type": "string",
                "description": "Fecha inicial en formato ISO 8601."
            },
            "fecha_fin": {
                "type": "string",
                "description": "Fecha final en formato ISO 8601."
            },
            "limite_ventas": {
                "type": "integer",
                "description": (
                    "Cantidad máxima de unidades vendidas "
                    "para considerar un producto de baja rotación."
                )
            }
        },
        "required": [
            "fecha_inicio",
            "fecha_fin",
            "limite_ventas"
        ],
        "additionalProperties": False
    },
    "strict": True
},
    {
    "type": "function",
    "name": "comparar_ventas",
    "description": (
        "Compara las ventas entre dos periodos. "
        "Devuelve ventas, pedidos, diferencia y "
        "porcentaje de cambio."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "periodo1_inicio": {
                "type": "string",
                "description": "Inicio del periodo actual en ISO 8601."
            },
            "periodo1_fin": {
                "type": "string",
                "description": "Fin del periodo actual en ISO 8601."
            },
            "periodo2_inicio": {
                "type": "string",
                "description": "Inicio del periodo anterior en ISO 8601."
            },
            "periodo2_fin": {
                "type": "string",
                "description": "Fin del periodo anterior en ISO 8601."
            }
        },
        "required": [
            "periodo1_inicio",
            "periodo1_fin",
            "periodo2_inicio",
            "periodo2_fin"
        ],
        "additionalProperties": False
    },
    "strict": True
},
{
    "type": "function",
    "name": "productos_para_reabastecer",
    "description": (
        "Obtiene los productos que necesitan atención "
        "por tener un stock igual o menor al límite indicado."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limite_stock": {
                "type": "integer",
                "description": "Stock máximo considerado bajo."
            }
        },
        "required": ["limite_stock"],
        "additionalProperties": False
    },
    "strict": True
},
{
    "type": "function",
    "name": "analizar_inventario",
    "description": (
        "Obtiene un resumen general del inventario: "
        "productos totales, agotados, con stock bajo y disponibles."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limite_stock": {
                "type": "integer",
                "description": "Límite utilizado para considerar stock bajo."
            }
        },
        "required": ["limite_stock"],
        "additionalProperties": False
    },
    "strict": True
},
    {
        "type": "function",
        "name": "buscar_producto",
        "description": (
            "Busca un medicamento o producto por nombre y devuelve "
            "precio, stock, descuento, categoría y demás información."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre del producto o medicamento."
                }
            },
            "required": ["nombre"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "productos_con_descuento",
        "description": "Obtiene los productos que actualmente tienen descuento.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "productos_stock_bajo",
        "description": (
            "Obtiene productos cuyo stock sea igual o menor "
            "al límite especificado."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Cantidad máxima considerada stock bajo."
                }
            },
            "required": ["limite"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "productos_mas_vendidos",
        "description": (
            "Obtiene los productos más vendidos dentro de un "
            "periodo determinado."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_inicio": {
                    "type": "string",
                    "description": "Fecha inicial en formato ISO 8601."
                },
                "fecha_fin": {
                    "type": "string",
                    "description": "Fecha final en formato ISO 8601."
                },
                "limite": {
                    "type": "integer",
                    "description": "Número máximo de productos."
                },
                "metrica": {
                    "type": "string",
                    "enum": ["cantidad", "ingresos"],
                    "description": "Usa cantidad para más unidades vendidas o ingresos para mayor dinero generado."
                }
            },
            "required": [
                "fecha_inicio",
                "fecha_fin",
                "limite",
                "metrica"
            ],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "ventas_totales",
        "description": (
            "Calcula ventas totales y cantidad de pedidos "
            "dentro de un periodo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_inicio": {
                    "type": "string",
                    "description": "Fecha inicial en formato ISO 8601."
                },
                "fecha_fin": {
                    "type": "string",
                    "description": "Fecha final en formato ISO 8601."
                }
            },
            "required": [
                "fecha_inicio",
                "fecha_fin"
            ],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "pedidos_por_estado",
        "description": (
            "Obtiene cuántos pedidos existen agrupados "
            "por estado."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    }
]


def _herramienta_periodo(nombre, descripcion, propiedades_adicionales=None, requeridos_adicionales=None):
    propiedades = {
        "fecha_inicio": {"type": "string", "description": "Inicio inclusivo del periodo en ISO 8601."},
        "fecha_fin": {"type": "string", "description": "Fin inclusivo del periodo en ISO 8601."}
    }
    propiedades.update(propiedades_adicionales or {})
    return {
        "type": "function", "name": nombre, "description": descripcion,
        "parameters": {"type": "object", "properties": propiedades,
                       "required": ["fecha_inicio", "fecha_fin"] + (requeridos_adicionales or []),
                       "additionalProperties": False},
        "strict": True
    }


ADMIN_TOOLS.extend([
    _herramienta_periodo(
        "reabastecimiento_priorizado",
        "Prioriza productos del catálogo que necesitan reabastecimiento cruzando stock actual con unidades vendidas e ingresos del periodo. Excluye productos exclusivos por encargo.",
        {"limite_stock": {"type": "integer", "description": "Stock máximo considerado bajo, normalmente 10."},
         "limite": {"type": "integer", "description": "Número máximo de productos, entre 1 y 100."}},
        ["limite_stock", "limite"]
    ),
    _herramienta_periodo(
        "ingresos_por_categoria",
        "Agrupa ingresos y unidades vendidas por la categoría actual del producto. Identifica por separado productos históricos fuera del catálogo."
    ),
    _herramienta_periodo(
        "ventas_por_dia",
        "Devuelve ingresos y número de pedidos por día; permite encontrar el día con mayores ventas y graficar la evolución."
    ),
    _herramienta_periodo(
        "analizar_pedidos",
        "Resume pedidos del periodo: cantidad total, completados, cancelados, pedidos que generan ingreso, ingresos, ticket promedio y distribución por estado."
    ),
    _herramienta_periodo(
        "evolucion_pedidos",
        "Devuelve por fecha la cantidad de pedidos, completados y cancelados para analizar su evolución."
    ),
    _herramienta_periodo(
        "analizar_encargos",
        "Resume encargos del periodo, total estimado y distribuciones por estado y tipo de entrega. Los encargos son solicitudes distintas de los pedidos de compra inmediata."
    )
])


def _rango(argumentos):
    inicio = datetime.fromisoformat(argumentos["fecha_inicio"])
    fin = datetime.fromisoformat(argumentos["fecha_fin"])
    if inicio > fin:
        raise ValueError("fecha_inicio no puede ser posterior a fecha_fin")
    return inicio, fin


def ejecutar_tool(nombre: str, argumentos: dict):

    if nombre in {"ingresos_por_categoria", "ventas_por_dia", "analizar_pedidos", "evolucion_pedidos", "analizar_encargos"}:
        inicio, fin = _rango(argumentos)
        funciones = {
            "ingresos_por_categoria": ingresos_por_categoria,
            "ventas_por_dia": ventas_por_dia,
            "analizar_pedidos": analizar_pedidos,
            "evolucion_pedidos": evolucion_pedidos,
            "analizar_encargos": analizar_encargos
        }
        return funciones[nombre](inicio, fin)

    if nombre == "reabastecimiento_priorizado":
        inicio, fin = _rango(argumentos)
        limite_stock = max(0, min(int(argumentos["limite_stock"]), 100000))
        limite = max(1, min(int(argumentos["limite"]), 100))
        return reabastecimiento_priorizado(inicio, fin, limite_stock, limite)

    if nombre == "analizar_oportunidades_oferta":
        return analizar_oportunidades_oferta(
            datetime.fromisoformat(
                argumentos["fecha_inicio"]
            ),
            datetime.fromisoformat(
                argumentos["fecha_fin"]
            ),
            argumentos["limite_ventas"],
            argumentos["stock_minimo"]
        )

    if nombre == "productos_baja_rotacion":
        return productos_baja_rotacion(
            datetime.fromisoformat(
                argumentos["fecha_inicio"]
            ),
            datetime.fromisoformat(
                argumentos["fecha_fin"]
            ),
            argumentos["limite_ventas"]
        )

    if nombre == "comparar_ventas":
        return comparar_ventas(
            datetime.fromisoformat(
                argumentos["periodo1_inicio"]
            ),
            datetime.fromisoformat(
                argumentos["periodo1_fin"]
            ),
            datetime.fromisoformat(
                argumentos["periodo2_inicio"]
            ),
            datetime.fromisoformat(
                argumentos["periodo2_fin"]
            )
        )

    if nombre == "productos_para_reabastecer":
        return productos_para_reabastecer(
            argumentos["limite_stock"]
        )

    if nombre == "analizar_inventario":
        return analizar_inventario(
            argumentos["limite_stock"]
        )

    if nombre == "buscar_producto":
        return buscar_producto(
            argumentos["nombre"]
        )

    if nombre == "productos_con_descuento":
        return productos_con_descuento()

    if nombre == "productos_stock_bajo":
        return productos_stock_bajo(
            argumentos["limite"]
        )

    if nombre == "productos_mas_vendidos":
        return productos_mas_vendidos(
            datetime.fromisoformat(argumentos["fecha_inicio"]),
            datetime.fromisoformat(argumentos["fecha_fin"]),
            argumentos["limite"],
            argumentos["metrica"]
        )

    if nombre == "ventas_totales":
        return ventas_totales(
            datetime.fromisoformat(argumentos["fecha_inicio"]),
            datetime.fromisoformat(argumentos["fecha_fin"])
        )

    if nombre == "pedidos_por_estado":
        return pedidos_por_estado()

    raise ValueError(
        f"Tool desconocida: {nombre}"
    )


def serializar_resultado(resultado):
    return json.dumps(
        resultado,
        ensure_ascii=False,
        default=str
    )
