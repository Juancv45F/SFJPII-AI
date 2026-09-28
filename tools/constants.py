ESTADOS_VENTA = ("pagado", "en_camino", "entregado")

# Los productos exclusivos por encargo mantienen stock cero por diseño y no
# representan existencias disponibles dentro del inventario físico.
FILTRO_INVENTARIO_FISICO = {"solo_encargo": {"$ne": True}}
ZONA_HORARIA_NEGOCIO = "America/Mexico_City"
