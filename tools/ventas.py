from database import db
from datetime import datetime
from tools.constants import ESTADOS_VENTA, FILTRO_INVENTARIO_FISICO, ZONA_HORARIA_NEGOCIO


def productos_mas_vendidos(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    limite: int = 10,
    metrica: str = "cantidad"
):
    campo_orden = "ingresos" if metrica == "ingresos" else "cantidad_vendida"
    pipeline = [
        {
            "$match": {
                "fecha": {
                    "$gte": fecha_inicio,
                    "$lte": fecha_fin
                },
                "estado": {
                    "$in": list(ESTADOS_VENTA)
                }
            }
        },
        {
            "$unwind": "$items"
        },
        {
            "$group": {
                "_id": "$items.productoId",
                "nombre": {
                    "$first": "$items.nombre"
                },
                "cantidad_vendida": {
                    "$sum": "$items.cantidad"
                },
                "ingresos": {
                    "$sum": "$items.subtotal"
                }
            }
        },
        {
            "$sort": {
                campo_orden: -1
            }
        },
        {
            "$limit": limite
        },
        {
            "$project": {
                "_id": 0,
                "productoId": {
                    "$toString": "$_id"
                },
                "_productoId": "$_id",
                "nombre": 1,
                "cantidad_vendida": 1,
                "ingresos": 1
            }
        }
    ]

    ventas = list(db.pedidos.aggregate(pipeline))
    # El pipeline histórico devuelve productoId como texto. Consultamos el
    # catálogo por los ObjectId originales desde una segunda agregación para
    # poder distinguir productos retirados sin perder sus ventas históricas.
    ids_catalogo = [item.get("_productoId") for item in ventas if item.get("_productoId") is not None]
    catalogo = list(db.productos.find({"_id": {"$in": ids_catalogo}},
                                     {"_id": 1, "stock": 1, "categoria.nombre": 1, "solo_encargo": 1}))
    por_id = {str(item["_id"]): item for item in catalogo}
    for item in ventas:
        item.pop("_productoId", None)
        producto = por_id.get(str(item.get("productoId", "")))
        item["en_catalogo"] = producto is not None
        item["stock_actual"] = producto.get("stock") if producto else None
        item["solo_encargo"] = bool(producto.get("solo_encargo", False)) if producto else None
        item["categoria_actual"] = producto.get("categoria", {}).get("nombre") if producto else None
        item["metrica_orden"] = metrica
    return ventas

def ventas_totales(
    fecha_inicio: datetime,
    fecha_fin: datetime
):
    pipeline = [
        {
            "$match": {
                "fecha": {
                    "$gte": fecha_inicio,
                    "$lte": fecha_fin
                },
                "estado": {
                    "$in": list(ESTADOS_VENTA)
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "total_ventas": {
                    "$sum": "$total"
                },
                "cantidad_pedidos": {
                    "$sum": 1
                }
            }
        },
        {
            "$project": {
                "_id": 0
            }
        }
    ]

    resultado = list(db.pedidos.aggregate(pipeline))

    if not resultado:
        return {
            "total_ventas": 0,
            "cantidad_pedidos": 0
        }

    return resultado[0]

def comparar_ventas(
    periodo1_inicio,
    periodo1_fin,
    periodo2_inicio,
    periodo2_fin
):
    periodo1 = ventas_totales(
        periodo1_inicio,
        periodo1_fin
    )

    periodo2 = ventas_totales(
        periodo2_inicio,
        periodo2_fin
    )

    total1 = periodo1.get("total_ventas", 0) if periodo1 else 0
    total2 = periodo2.get("total_ventas", 0) if periodo2 else 0

    diferencia = total1 - total2

    if total2 > 0:
        porcentaje_cambio = (
            (diferencia / total2) * 100
        )
    else:
        porcentaje_cambio = None

    return {
        "periodo_actual": periodo1,
        "periodo_anterior": periodo2,
        "diferencia": round(diferencia, 2),
        "porcentaje_cambio": (
            round(porcentaje_cambio, 2)
            if porcentaje_cambio is not None
            else None
        )
    }


def ingresos_por_categoria(fecha_inicio, fecha_fin):
    return list(db.pedidos.aggregate([
        {"$match": {"fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}, "estado": {"$in": list(ESTADOS_VENTA)}}},
        {"$unwind": "$items"},
        {"$lookup": {"from": "productos", "localField": "items.productoId", "foreignField": "_id", "as": "producto_actual"}},
        {"$unwind": {"path": "$producto_actual", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": {"$ifNull": ["$producto_actual.categoria.nombre", "Fuera del catálogo / sin categoría"]},
            "ingresos": {"$sum": "$items.subtotal"}, "unidades_vendidas": {"$sum": "$items.cantidad"}
        }},
        {"$sort": {"ingresos": -1}},
        {"$project": {"_id": 0, "categoria": "$_id", "ingresos": {"$round": ["$ingresos", 2]}, "unidades_vendidas": 1}}
    ]))


def ventas_por_dia(fecha_inicio, fecha_fin):
    return list(db.pedidos.aggregate([
        {"$match": {"fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}, "estado": {"$in": list(ESTADOS_VENTA)}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha", "timezone": ZONA_HORARIA_NEGOCIO}},
            "ingresos": {"$sum": "$total"}, "pedidos": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "fecha": "$_id", "ingresos": {"$round": ["$ingresos", 2]}, "pedidos": 1}}
    ]))


def productos_baja_rotacion(
    fecha_inicio,
    fecha_fin,
    limite_ventas: int = 2
):
    pipeline = [
        {
            "$match": {
                "fecha": {
                    "$gte": fecha_inicio,
                    "$lte": fecha_fin
                },
                "estado": {
                    "$in": list(ESTADOS_VENTA)
                }
            }
        },
        {
            "$unwind": "$items"
        },
        {
            "$group": {
                "_id": "$items.productoId",
                "cantidad_vendida": {
                    "$sum": "$items.cantidad"
                }
            }
        }
    ]

    ventas = list(
        db.pedidos.aggregate(pipeline)
    )

    # Relacionamos las ventas mediante ObjectId,
    # no mediante el nombre del producto.
    ventas_por_producto = {
        venta["_id"]: venta["cantidad_vendida"]
        for venta in ventas
    }

    productos = list(
        db.productos.find(
            FILTRO_INVENTARIO_FISICO,
            {
                "_id": 1,
                "nombre": 1,
                "stock": 1,
                "precio": 1,
                "descuento": 1
            }
        )
    )

    resultado = []

    for producto in productos:

        cantidad_vendida = ventas_por_producto.get(
            producto["_id"],
            0
        )

        if cantidad_vendida <= limite_ventas:
            resultado.append({
                "producto_id": str(producto["_id"]),
                "nombre": producto.get(
                    "nombre",
                    "Sin nombre"
                ),
                "precio": producto.get(
                    "precio",
                    0
                ),
                "descuento": producto.get(
                    "descuento",
                    0
                ),
                "stock": producto.get(
                    "stock",
                    0
                ),
                "cantidad_vendida": cantidad_vendida
            })

    resultado.sort(
        key=lambda producto: (
            producto["cantidad_vendida"],
            -producto["stock"]
        )
    )

    return resultado

def analizar_oportunidades_oferta(
    fecha_inicio,
    fecha_fin,
    limite_ventas: int = 2,
    stock_minimo: int = 1
):
    productos = productos_baja_rotacion(
        fecha_inicio,
        fecha_fin,
        limite_ventas
    )

    candidatos = []

    for producto in productos:

        stock = producto.get("stock", 0)
        descuento = producto.get("descuento", 0)
        cantidad_vendida = producto.get(
            "cantidad_vendida",
            0
        )

        # No tiene sentido recomendar una oferta
        # para un producto agotado.
        if stock < stock_minimo:
            continue

        candidatos.append({
            "producto_id": producto.get(
                "producto_id"
            ),
            "nombre": producto.get(
                "nombre"
            ),
            "precio": producto.get(
                "precio",
                0
            ),
            "stock": stock,
            "cantidad_vendida": cantidad_vendida,
            "descuento_actual": descuento,
            "motivo": (
                "Tiene inventario disponible y "
                "pocas ventas en el periodo analizado."
            )
        })

    # Primero mostramos productos con más stock
    # y menor cantidad de ventas.
    candidatos.sort(
        key=lambda producto: (
            producto["cantidad_vendida"],
            -producto["stock"]
        )
    )

    return candidatos
