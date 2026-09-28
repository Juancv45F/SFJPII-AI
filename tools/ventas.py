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