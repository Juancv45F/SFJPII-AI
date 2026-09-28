import json
from datetime import datetime

from tools.productos import (
    buscar_producto,
    productos_con_descuento
)
from tools.inventario import productos_stock_bajo
from tools.ventas import (
    productos_mas_vendidos,
    ventas_totales
)
from tools.pedidos import pedidos_por_estado


ADMIN_TOOLS = [
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
                }
            },
            "required": [
                "fecha_inicio",
                "fecha_fin",
                "limite"
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


def ejecutar_tool(nombre: str, argumentos: dict):

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
            argumentos["limite"]
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