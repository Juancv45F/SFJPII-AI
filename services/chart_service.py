def crear_grafica(
    tool_name: str,
    resultado
):
    if not resultado:
        return None

    if tool_name == "productos_mas_vendidos":

        labels = []
        data = []

        for producto in resultado:
            labels.append(
                producto.get("nombre", "Sin nombre")
            )

            data.append(
                producto.get("cantidad_vendida", 0)
            )

        return {
            "tipo": "bar",
            "titulo": "Productos más vendidos",
            "labels": labels,
            "data": data
        }

    if tool_name == "pedidos_por_estado":

        labels = []
        data = []

        for estado in resultado:
            labels.append(
                estado.get("estado", "Desconocido")
            )

            data.append(
                estado.get("cantidad", 0)
            )

        return {
            "tipo": "doughnut",
            "titulo": "Pedidos por estado",
            "labels": labels,
            "data": data
        }

    if tool_name == "comparar_ventas":
        return grafica_comparar_ventas(resultado)

    if tool_name == "analizar_inventario":
        return grafica_inventario(resultado)

    return None

def grafica_comparar_ventas(resultado):
    if not resultado:
        return None

    periodo_actual = resultado.get("periodo_actual", {})
    periodo_anterior = resultado.get("periodo_anterior", {})

    return {
        "tipo": "bar",
        "titulo": "Comparación de ventas",
        "labels": [
            "Periodo actual",
            "Periodo anterior"
        ],
        "data": [
            periodo_actual.get("total_ventas", 0),
            periodo_anterior.get("total_ventas", 0)
        ]
    }

def grafica_inventario(resultado):
    if not resultado:
        return None

    return {
        "tipo": "doughnut",
        "titulo": "Estado del inventario",
        "labels": [
            "Agotados",
            "Stock bajo",
            "Disponibles"
        ],
        "data": [
            resultado.get("agotados", 0),
            resultado.get("stock_bajo", 0),
            resultado.get("disponibles", 0)
        ]
    }
