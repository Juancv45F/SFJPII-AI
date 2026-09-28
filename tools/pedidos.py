from database import db
from tools.ventas import ESTADOS_VALIDOS


def pedidos_por_estado(fecha_inicio=None, fecha_fin=None):
    filtro = {}
    if fecha_inicio is not None and fecha_fin is not None:
        filtro["fecha"] = {"$gte": fecha_inicio, "$lte": fecha_fin}
    pipeline = [
        {"$match": filtro},
        {
            "$group": {
                "_id": "$estado",
                "cantidad": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "cantidad": -1
            }
        },
        {
            "$project": {
                "_id": 0,
                "estado": "$_id",
                "cantidad": 1
            }
        }
    ]

    return list(db.pedidos.aggregate(pipeline))


def analizar_pedidos(fecha_inicio, fecha_fin):
    estados = pedidos_por_estado(fecha_inicio, fecha_fin)
    resumen = list(db.pedidos.aggregate([
        {"$match": {"fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}}},
        {"$group": {"_id": None,
            "total_pedidos": {"$sum": 1},
            "pedidos_completados": {"$sum": {"$cond": [{"$eq": ["$estado", "entregado"]}, 1, 0]}},
            "pedidos_cancelados": {"$sum": {"$cond": [{"$eq": ["$estado", "cancelado"]}, 1, 0]}},
            "pedidos_con_ingreso": {"$sum": {"$cond": [{"$in": ["$estado", ESTADOS_VALIDOS]}, 1, 0]}},
            "ingresos": {"$sum": {"$cond": [{"$in": ["$estado", ESTADOS_VALIDOS]}, "$total", 0]}}
        }},
        {"$project": {"_id": 0}}
    ]))
    datos = resumen[0] if resumen else {"total_pedidos": 0, "pedidos_completados": 0,
                                        "pedidos_cancelados": 0, "pedidos_con_ingreso": 0, "ingresos": 0}
    con_ingreso = datos.get("pedidos_con_ingreso", 0)
    datos["ingresos"] = round(float(datos.get("ingresos", 0)), 2)
    datos["ticket_promedio"] = round(datos["ingresos"] / con_ingreso, 2) if con_ingreso else 0
    datos["por_estado"] = estados
    return datos


def evolucion_pedidos(fecha_inicio, fecha_fin):
    return list(db.pedidos.aggregate([
        {"$match": {"fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha",
                                                  "timezone": "America/Mexico_City"}},
                    "pedidos": {"$sum": 1},
                    "completados": {"$sum": {"$cond": [{"$eq": ["$estado", "entregado"]}, 1, 0]}},
                    "cancelados": {"$sum": {"$cond": [{"$eq": ["$estado", "cancelado"]}, 1, 0]}}}},
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "fecha": "$_id", "pedidos": 1, "completados": 1, "cancelados": 1}}
    ]))


def analizar_encargos(fecha_inicio, fecha_fin):
    documentos = list(db.encargos.aggregate([
        {"$match": {"createdAt": {"$gte": fecha_inicio, "$lte": fecha_fin}}},
        {"$facet": {
            "estados": [{"$group": {"_id": "$estado", "cantidad": {"$sum": 1}}}, {"$sort": {"cantidad": -1}}],
            "entregas": [{"$group": {"_id": "$tipo_entrega", "cantidad": {"$sum": 1}}}, {"$sort": {"cantidad": -1}}],
            "totales": [{"$group": {"_id": None, "total_encargos": {"$sum": 1},
                                        "total_estimado": {"$sum": "$total_estimado"}}}]
        }}
    ]))
    facet = documentos[0] if documentos else {"estados": [], "entregas": [], "totales": []}
    total = facet.get("totales", [{}])[0] if facet.get("totales") else {}
    return {
        "total_encargos": total.get("total_encargos", 0),
        "total_estimado": round(float(total.get("total_estimado", 0)), 2),
        "por_estado": [{"estado": x.get("_id", "desconocido"), "cantidad": x.get("cantidad", 0)} for x in facet.get("estados", [])],
        "por_tipo_entrega": [{"tipo_entrega": x.get("_id", "desconocido"), "cantidad": x.get("cantidad", 0)} for x in facet.get("entregas", [])]
    }
