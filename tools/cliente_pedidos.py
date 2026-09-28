from bson import ObjectId

from database import db
from tools.validators import ToolValidationError


ESTADOS_PEDIDO_CLIENTE = {
    "pendiente", "pagado", "en_camino", "entregado", "cancelado"
}
ESTADOS_ENCARGO_CLIENTE = {
    "pendiente", "disponible", "en_camino", "entregado", "cancelado"
}


def _object_id(valor: str, nombre: str) -> ObjectId:
    if not isinstance(valor, str) or not ObjectId.is_valid(valor):
        raise ToolValidationError(f"{nombre} no es válido")
    return ObjectId(valor)


def _estado(valor, permitidos: set[str], nombre: str):
    if valor is None:
        return None
    estado = str(valor).strip().lower()
    if estado not in permitidos:
        raise ToolValidationError(f"{nombre} no es válido")
    return estado


def _item(item: dict) -> dict:
    return {
        "producto_id": str(item.get("productoId")) if item.get("productoId") else None,
        "nombre": item.get("nombre", "Producto"),
        "cantidad": item.get("cantidad", 0),
        "precio_unitario": item.get("precio_unitario", 0),
        "subtotal": item.get("subtotal"),
    }


def consultar_mis_pedidos(user_id: str, estado=None, limite: int = 10) -> list[dict]:
    filtro = {"userId": _object_id(user_id, "usuario")}
    estado_normalizado = _estado(estado, ESTADOS_PEDIDO_CLIENTE, "estado")
    if estado_normalizado:
        filtro["estado"] = estado_normalizado

    documentos = db.pedidos.find(
        filtro,
        {
            "_id": 1,
            "fecha": 1,
            "createdAt": 1,
            "total": 1,
            "estado": 1,
            "metodo_pago": 1,
            "items.nombre": 1,
            "items.cantidad": 1,
        },
    ).sort([("createdAt", -1), ("fecha", -1)]).limit(limite)

    return [
        {
            "pedido_id": str(documento["_id"]),
            "fecha": documento.get("fecha") or documento.get("createdAt"),
            "estado": documento.get("estado"),
            "total": documento.get("total", 0),
            "metodo_pago": documento.get("metodo_pago"),
            "productos": [
                {"nombre": item.get("nombre", "Producto"), "cantidad": item.get("cantidad", 0)}
                for item in documento.get("items", [])
            ],
        }
        for documento in documentos
    ]


def consultar_mi_pedido(user_id: str, pedido_id: str) -> dict:
    documento = db.pedidos.find_one(
        {
            "_id": _object_id(pedido_id, "pedido_id"),
            "userId": _object_id(user_id, "usuario"),
        },
        {
            "_id": 1,
            "fecha": 1,
            "createdAt": 1,
            "total": 1,
            "estado": 1,
            "metodo_pago": 1,
            "ubicacion": 1,
            "items": 1,
        },
    )
    if not documento:
        return {"encontrado": False, "mensaje": "No se encontró ese pedido entre tus pedidos."}

    return {
        "encontrado": True,
        "pedido": {
            "pedido_id": str(documento["_id"]),
            "fecha": documento.get("fecha") or documento.get("createdAt"),
            "estado": documento.get("estado"),
            "total": documento.get("total", 0),
            "metodo_pago": documento.get("metodo_pago"),
            "ubicacion": documento.get("ubicacion"),
            "productos": [_item(item) for item in documento.get("items", [])],
        },
    }


def consultar_mis_encargos(user_id: str, estado=None, limite: int = 10) -> list[dict]:
    filtro = {"userId": _object_id(user_id, "usuario")}
    estado_normalizado = _estado(estado, ESTADOS_ENCARGO_CLIENTE, "estado")
    if estado_normalizado:
        filtro["estado"] = estado_normalizado

    documentos = db.encargos.find(
        filtro,
        {
            "_id": 1,
            "createdAt": 1,
            "updatedAt": 1,
            "total_estimado": 1,
            "estado": 1,
            "tipo_entrega": 1,
            "ubicacion.alias": 1,
            "motivo_cancelacion": 1,
            "disponibleAt": 1,
            "items": 1,
        },
    ).sort([("createdAt", -1)]).limit(limite)

    return [
        {
            "encargo_id": str(documento["_id"]),
            "fecha": documento.get("createdAt"),
            "actualizado": documento.get("updatedAt"),
            "estado": documento.get("estado"),
            "total_estimado": documento.get("total_estimado", 0),
            "tipo_entrega": documento.get("tipo_entrega"),
            "ubicacion_alias": (documento.get("ubicacion") or {}).get("alias"),
            "disponible_desde": documento.get("disponibleAt"),
            "motivo_cancelacion": documento.get("motivo_cancelacion"),
            "productos": [_item(item) for item in documento.get("items", [])],
        }
        for documento in documentos
    ]
