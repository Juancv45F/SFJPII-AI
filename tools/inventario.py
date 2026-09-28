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