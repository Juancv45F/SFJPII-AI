from database import db


def pedidos_por_estado():
    pipeline = [
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