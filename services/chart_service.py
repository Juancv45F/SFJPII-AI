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

    return None