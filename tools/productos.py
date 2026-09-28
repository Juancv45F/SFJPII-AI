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

    # El producto ya no existe en el catálogo actual
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

    # -----------------------------
    # Precio y descuento
    # -----------------------------

    precio = float(producto.get("precio", 0) or 0)
    descuento_porcentaje = float(
        producto.get("descuento", 0) or 0
    )

    # El descuento debe estar entre 0% y 100%
    descuento_porcentaje = max(
        0,
        min(descuento_porcentaje, 100)
    )

    monto_descuento = (
        precio * descuento_porcentaje / 100
    )

    precio_final = (
        precio - monto_descuento
    )

    # Agregamos información calculada
    producto["precio"] = round(precio, 2)

    producto["descuento_porcentaje"] = round(
        descuento_porcentaje,
        2
    )

    producto["monto_descuento"] = round(
        monto_descuento,
        2
    )

    producto["precio_final"] = round(
        precio_final,
        2
    )

    # Quitamos el campo original para evitar
    # que la IA interprete "15" como $15
    producto.pop("descuento", None)

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
                "descripcion": 1,
                "precio": 1,
                "descuento": 1,
                "stock": 1,
                "solo_encargo": 1,
                "requiere_receta": 1,
                "categoria.nombre": 1
            }
        )
    )

def productos_por_categoria(
    categoria: str,
    limite: int = 20
):
    productos = db.productos.find(
        {
            "categoria.nombre": {
                "$regex": f"^{categoria}$",
                "$options": "i"
            },
            "categoria.activa": True
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
            "categoria.nombre": 1
        }
    ).limit(limite)

    return list(productos)


def buscar_productos(
    busqueda: str,
    limite: int = 10
):
    productos = db.productos.find(
        {
            "$or": [
                {
                    "nombre": {
                        "$regex": busqueda,
                        "$options": "i"
                    }
                },
                {
                    "descripcion": {
                        "$regex": busqueda,
                        "$options": "i"
                    }
                },
                {
                    "categoria.nombre": {
                        "$regex": busqueda,
                        "$options": "i"
                    }
                }
            ]
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
            "categoria.nombre": 1
        }
    ).limit(limite)

    return list(productos)