from database import db
from datetime import datetime


ESTADOS_VALIDOS = [
    "pagado",
    "en_camino",
    "entregado"
]


def productos_mas_vendidos(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    limite: int = 10
):
    pipeline = [
        {
            "$match": {
                "fecha": {
                    "$gte": fecha_inicio,
                    "$lte": fecha_fin
                },
                "estado": {
                    "$in": ESTADOS_VALIDOS
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
                "cantidad_vendida": -1
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
                "nombre": 1,
                "cantidad_vendida": 1,
                "ingresos": 1
            }
        }
    ]

    return list(db.pedidos.aggregate(pipeline))

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
                    "$in": ESTADOS_VALIDOS
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
                    "$in": ESTADOS_VALIDOS
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
            {},
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