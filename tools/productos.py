from database import db


def _normalizar_precio_producto(producto: dict) -> dict:
    """
    Normaliza la información de precio y descuento de un producto.

    El campo 'descuento' almacenado en MongoDB se interpreta
    como porcentaje.

    Ejemplo:
        precio = 95
        descuento = 15

    Resultado:
        precio = 95.00
        descuento_porcentaje = 15.00
        monto_descuento = 14.25
        precio_final = 80.75
    """

    precio = float(
        producto.get("precio", 0) or 0
    )

    descuento_porcentaje = float(
        producto.get("descuento", 0) or 0
    )

    # Evitamos descuentos inválidos:
    # menor a 0% o mayor a 100%.
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

    producto["precio"] = round(
        precio,
        2
    )

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

    # Eliminamos el campo original para evitar que la IA
    # interprete, por ejemplo, descuento=15 como $15.
    producto.pop(
        "descuento",
        None
    )

    return producto


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

    # El producto ya no existe en el catálogo actual.
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

    producto = _normalizar_precio_producto(
        producto
    )

    return {
        "encontrado": True,
        "estado": "disponible_en_catalogo",
        "producto": producto
    }


def productos_con_descuento():
    productos = list(
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

    return [
        _normalizar_precio_producto(producto)
        for producto in productos
    ]


def productos_por_categoria(
    categoria: str,
    limite: int = 20
):
    productos = list(
        db.productos.find(
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
    )

    return [
        _normalizar_precio_producto(producto)
        for producto in productos
    ]


def buscar_productos(
    busqueda: str,
    limite: int = 10
):
    productos = list(
        db.productos.find(
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
    )

    return [
        _normalizar_precio_producto(producto)
        for producto in productos
    ]