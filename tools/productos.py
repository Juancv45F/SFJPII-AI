from database import db


def buscar_producto(nombre: str):
    producto = db.productos.find_one(
        {
            "nombre": {
                "$regex": nombre,
                "$options": "i"
            }
        },
        {
            "_id": 0,
            "nombre": 1,
            "descripcion": 1,
            "precio": 1,
            "descuento": 1,
            "stock": 1,
            "solo_encargo": 1,
            "requiere_receta": 1,

            # No devolvemos categoria._id
            "categoria.nombre": 1,
            "categoria.descripcion": 1,
            "categoria.activa": 1
        }
    )

    return producto


def productos_con_descuento():
    return list(
        db.productos.find(
            {
                "descuento": {
                    "$gt": 0
                }
            },
            {
                "_id": 0,
                "nombre": 1,
                "precio": 1,
                "descuento": 1,
                "stock": 1
            }
        )
    )