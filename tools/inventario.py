from database import db


def productos_stock_bajo(limite: int = 10):
    productos = db.productos.find(
        {
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
                }
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
    total_productos = db.productos.count_documents({})

    agotados = db.productos.count_documents({
        "stock": 0
    })

    stock_bajo = db.productos.count_documents({
        "stock": {
            "$gt": 0,
            "$lte": limite_stock
        }
    })

    disponibles = db.productos.count_documents({
        "stock": {
            "$gt": limite_stock
        }
    })

    return {
        "total_productos": total_productos,
        "agotados": agotados,
        "stock_bajo": stock_bajo,
        "disponibles": disponibles,
        "limite_stock_bajo": limite_stock
    }