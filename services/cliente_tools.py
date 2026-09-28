from tools.productos import (
    buscar_producto,
    buscar_productos,
    productos_por_categoria,
    productos_con_descuento
)

from tools.validators import entero_limite
from tools.cliente_pedidos import (
    consultar_mis_pedidos,
    consultar_mi_pedido,
    consultar_mis_encargos,
)
from tools.informacion_farmacia import consultar_informacion_farmacia

CLIENTE_TOOLS = [
    {
        "type": "function",
        "name": "buscar_producto",
        "description": (
            "Busca un producto específico en el catálogo actual de la farmacia "
            "por su nombre. Úsala cuando el cliente pregunte por un producto "
            "concreto, su precio, stock, descuento, disponibilidad, si es por "
            "encargo o si requiere receta."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre del producto a buscar."
                }
            },
            "required": ["nombre"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "buscar_productos",
        "description": (
            "Busca productos del catálogo por nombre, descripción o categoría. "
            "Úsala para búsquedas generales como 'shampoo', 'dolor' o "
            "'cuidado personal'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "busqueda": {
                    "type": "string",
                    "description": "Texto que desea buscar el cliente."
                },
                "limite": {
                    "type": "integer",
                    "description": "Cantidad máxima de resultados.",
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["busqueda"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "productos_por_categoria",
        "description": (
            "Obtiene productos pertenecientes a una categoría específica "
            "del catálogo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "categoria": {
                    "type": "string",
                    "description": "Nombre de la categoría."
                },
                "limite": {
                    "type": "integer",
                    "description": "Cantidad máxima de resultados.",
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["categoria"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "productos_con_descuento",
        "description": (
            "Obtiene los productos que actualmente tienen un descuento."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "consultar_informacion_farmacia",
        "description": (
            "Consulta el documento editable y vigente de la farmacia para responder "
            "sobre teléfonos, WhatsApp, dirección, horario regular y excepciones de horario."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "consultar_mis_pedidos",
        "description": "Consulta únicamente los pedidos del cliente autenticado, opcionalmente filtrados por estado.",
        "parameters": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "enum": ["pendiente", "pagado", "en_camino", "entregado", "cancelado"]
                },
                "limite": {"type": "integer", "minimum": 1, "maximum": 20}
            },
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "consultar_mi_pedido",
        "description": "Consulta el detalle de un pedido si pertenece al cliente autenticado.",
        "parameters": {
            "type": "object",
            "properties": {
                "pedido_id": {"type": "string", "description": "Identificador del pedido."}
            },
            "required": ["pedido_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "consultar_mis_encargos",
        "description": "Consulta únicamente los encargos del cliente autenticado, opcionalmente filtrados por estado.",
        "parameters": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "enum": ["pendiente", "disponible", "en_camino", "entregado", "cancelado"]
                },
                "limite": {"type": "integer", "minimum": 1, "maximum": 20}
            },
            "additionalProperties": False
        }
    }
]

def ejecutar_cliente_tool(
    nombre: str,
    argumentos: dict,
    user_id: str
):
    if nombre == "buscar_producto":
        return buscar_producto(
            argumentos["nombre"]
        )

    if nombre == "buscar_productos":
        limite = entero_limite(
            argumentos.get("limite", 10),
            "limite",
            1,
            20
        )

        return buscar_productos(
            argumentos["busqueda"],
            limite
        )

    if nombre == "productos_por_categoria":
        limite = entero_limite(
            argumentos.get("limite", 20),
            "limite",
            1,
            20
        )

        return productos_por_categoria(
            argumentos["categoria"],
            limite
        )

    if nombre == "productos_con_descuento":
        return productos_con_descuento()

    if nombre == "consultar_informacion_farmacia":
        return consultar_informacion_farmacia()

    if nombre == "consultar_mis_pedidos":
        return consultar_mis_pedidos(
            user_id,
            argumentos.get("estado"),
            entero_limite(argumentos.get("limite", 10), "limite", 1, 20),
        )

    if nombre == "consultar_mi_pedido":
        return consultar_mi_pedido(user_id, argumentos["pedido_id"])

    if nombre == "consultar_mis_encargos":
        return consultar_mis_encargos(
            user_id,
            argumentos.get("estado"),
            entero_limite(argumentos.get("limite", 10), "limite", 1, 20),
        )

    raise ValueError(
        f"Tool de cliente no permitida: {nombre}"
    )
