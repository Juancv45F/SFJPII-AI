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

            "categoria.nombre": 1,
            "categoria.descripcion": 1,
            "categoria.activa": 1
        }
    )

    if producto is None:
        return {
            "encontrado": False,
            "nombre_buscado": nombre,
            "estado": "no_disponible_en_catalogo",
            "mensaje": (
                f"El producto '{nombre}' no se encuentra actualmente "
                "en el catálogo. Puede aparecer en el historial de pedidos "
                "si fue vendido anteriormente."
            )
        }

    return {
        "encontrado": True,
        "estado": "disponible_en_catalogo",
        "producto": producto
    }
    
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