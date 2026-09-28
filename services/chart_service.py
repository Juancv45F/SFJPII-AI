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

            data.append(producto.get("ingresos", 0) if producto.get("metrica_orden") == "ingresos"
                        else producto.get("cantidad_vendida", 0))

        return {
            "tipo": "bar",
            "titulo": "Ingresos por producto" if resultado[0].get("metrica_orden") == "ingresos" else "Productos más vendidos",
            "labels": labels,
            "data": data,
            "unidad": "MXN" if resultado[0].get("metrica_orden") == "ingresos" else "unidades"
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
            "data": data,
            "unidad": "pedidos"
        }

    if tool_name == "comparar_ventas":
        return grafica_comparar_ventas(resultado)

    if tool_name == "analizar_inventario":
        return grafica_inventario(resultado)

    if tool_name == "reabastecimiento_priorizado":
        return {"tipo": "bar", "titulo": "Ventas de productos por reabastecer",
                "labels": [x.get("nombre", "Sin nombre") for x in resultado],
                "data": [x.get("cantidad_vendida", 0) for x in resultado], "unidad": "unidades"}

    if tool_name == "ingresos_por_categoria":
        return {"tipo": "bar", "titulo": "Ingresos por categoría",
                "labels": [x.get("categoria", "Sin categoría") for x in resultado],
                "data": [x.get("ingresos", 0) for x in resultado], "unidad": "MXN"}

    if tool_name == "ventas_por_dia":
        return {"tipo": "bar", "titulo": "Ingresos por día",
                "labels": [x.get("fecha", "Sin fecha") for x in resultado],
                "data": [x.get("ingresos", 0) for x in resultado], "unidad": "MXN"}

    if tool_name == "analizar_pedidos":
        estados = resultado.get("por_estado", [])
        return {"tipo": "doughnut", "titulo": "Pedidos por estado",
                "labels": [x.get("estado", "Desconocido") for x in estados],
                "data": [x.get("cantidad", 0) for x in estados], "unidad": "pedidos"} if estados else None

    if tool_name == "evolucion_pedidos":
        return {"tipo": "bar", "titulo": "Evolución de pedidos",
                "labels": [x.get("fecha", "Sin fecha") for x in resultado],
                "data": [x.get("pedidos", 0) for x in resultado], "unidad": "pedidos"}

    if tool_name == "analizar_encargos":
        estados = resultado.get("por_estado", [])
        return {"tipo": "doughnut", "titulo": "Encargos por estado",
                "labels": [x.get("estado", "Desconocido") for x in estados],
                "data": [x.get("cantidad", 0) for x in estados], "unidad": "encargos"} if estados else None

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
        ],
        "unidad": "MXN"
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
        ],
        "unidad": "productos"
    }
