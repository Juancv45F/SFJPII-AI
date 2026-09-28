from database import db
from tools.constants import ESTADOS_VENTA, FILTRO_INVENTARIO_FISICO


def productos_stock_bajo(limite: int = 10):
    productos = db.productos.find(
        {
            **FILTRO_INVENTARIO_FISICO,
            "stock": {
                "$lte": limite
            }
        },
        {
            "_id": 0,
            "nombre": 1,
            "stock": 1,
            "precio": 1
        }
    ).sort("stock", 1)

    return list(productos)

def productos_para_reabastecer(limite_stock: int = 10):
    return list(
        db.productos.find(
            {
                "stock": {
                    "$lte": limite_stock
                },
                **FILTRO_INVENTARIO_FISICO
            },
            {
                "_id": 0,
                "nombre": 1,
                "stock": 1,
                "precio": 1,
                "descuento": 1,
                "solo_encargo": 1
            }
        ).sort("stock", 1)
    )

def analizar_inventario(limite_stock: int = 10):
    total_productos = db.productos.count_documents(FILTRO_INVENTARIO_FISICO)

    agotados = db.productos.count_documents({**FILTRO_INVENTARIO_FISICO,
        "stock": 0
    })

    stock_bajo = db.productos.count_documents({**FILTRO_INVENTARIO_FISICO,
        "stock": {
            "$gt": 0,
            "$lte": limite_stock
        }
    })

    disponibles = db.productos.count_documents({**FILTRO_INVENTARIO_FISICO,
        "stock": {
            "$gt": limite_stock
        }
    })

    return {
        "total_productos": total_productos,
        "agotados": agotados,
        "stock_bajo": stock_bajo,
        "disponibles": disponibles,
        "limite_stock_bajo": limite_stock,
        "productos_solo_encargo_excluidos": db.productos.count_documents({"solo_encargo": True})
    }


def reabastecimiento_priorizado(fecha_inicio, fecha_fin, limite_stock: int = 10, limite: int = 20):
    """Cruza el inventario actual con ventas reales del periodo.

    Los productos exclusivos por encargo mantienen stock cero por diseño, por
    lo que no se incluyen como recomendaciones de inventario físico.
    """
    ventas = list(db.pedidos.aggregate([
        {"$match": {"fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}, "estado": {"$in": list(ESTADOS_VENTA)}}},
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.productoId", "cantidad_vendida": {"$sum": "$items.cantidad"},
                    "ingresos": {"$sum": "$items.subtotal"}}}
    ]))
    ventas_por_id = {item["_id"]: item for item in ventas}
    productos = db.productos.find(
        {"stock": {"$lte": limite_stock}, **FILTRO_INVENTARIO_FISICO},
        {"_id": 1, "nombre": 1, "stock": 1, "precio": 1, "categoria.nombre": 1}
    )
    resultado = []
    for producto in productos:
        venta = ventas_por_id.get(producto["_id"], {})
        stock = int(producto.get("stock", 0))
        cantidad = int(venta.get("cantidad_vendida", 0))
        resultado.append({
            "producto_id": str(producto["_id"]),
            "nombre": producto.get("nombre", "Sin nombre"),
            "stock": stock,
            "categoria": producto.get("categoria", {}).get("nombre", "Sin categoría"),
            "cantidad_vendida": cantidad,
            "ingresos": round(float(venta.get("ingresos", 0)), 2),
            "prioridad": "urgente" if stock == 0 and cantidad > 0 else "alta" if cantidad > 0 else "media",
            "motivo": "Agotado con ventas en el periodo" if stock == 0 and cantidad > 0
                      else "Stock bajo con ventas en el periodo" if cantidad > 0
                      else "Stock bajo sin ventas registradas en el periodo"
        })
    resultado.sort(key=lambda item: (item["prioridad"] != "urgente", item["prioridad"] != "alta",
                                     -item["cantidad_vendida"], item["stock"], item["nombre"].lower()))
    return resultado[:max(1, min(limite, 100))]
