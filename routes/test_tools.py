from fastapi import APIRouter, Query
from datetime import datetime
from database import db

from tools.productos import buscar_producto, productos_con_descuento
from tools.inventario import productos_stock_bajo
from tools.ventas import analizar_oportunidades_oferta, productos_mas_vendidos, ventas_totales
from tools.pedidos import pedidos_por_estado
from tools.ventas import (
    comparar_ventas,
    productos_baja_rotacion,
    analizar_oportunidades_oferta
)

from tools.inventario import (
    productos_para_reabastecer,
    analizar_inventario
)


router = APIRouter(
    prefix="/test",
    tags=["Pruebas"]
)


@router.get("/buscar-producto")
def test_buscar_producto(nombre: str = Query(...)):
    resultado = buscar_producto(nombre)

    return {
        "resultado": resultado
    }


@router.get("/productos-descuento")
def test_productos_descuento():
    return {
        "resultados": productos_con_descuento()
    }


@router.get("/stock-bajo")
def test_stock_bajo(limite: int = 10):
    return {
        "limite": limite,
        "resultados": productos_stock_bajo(limite)
    }


@router.get("/pedidos-estado")
def test_pedidos_estado():
    return {
        "resultados": pedidos_por_estado()
    }


@router.get("/productos-mas-vendidos")
def test_productos_mas_vendidos(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    limite: int = 10
):
    return {
        "resultados": productos_mas_vendidos(
            fecha_inicio,
            fecha_fin,
            limite
        )
    }


@router.get("/ventas")
def test_ventas(
    fecha_inicio: datetime,
    fecha_fin: datetime
):
    return ventas_totales(
        fecha_inicio,
        fecha_fin
    )

@router.get("/colecciones")
def test_colecciones():
    return {
        "database": db.name,
        "colecciones": db.list_collection_names()
    }


@router.get("/comparar-ventas")
def test_comparar_ventas(
    inicio1: datetime,
    fin1: datetime,
    inicio2: datetime,
    fin2: datetime
):
    return {
        "resultado": comparar_ventas(
            inicio1,
            fin1,
            inicio2,
            fin2
        )
    }


@router.get("/baja-rotacion")
def test_baja_rotacion(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    limite_ventas: int = 2
):
    return {
        "resultado": productos_baja_rotacion(
            fecha_inicio,
            fecha_fin,
            limite_ventas
        )
    }


@router.get("/reabastecer")
def test_reabastecer(
    limite_stock: int = 10
):
    return {
        "resultado": productos_para_reabastecer(
            limite_stock
        )
    }


@router.get("/analizar-inventario")
def test_analizar_inventario(
    limite_stock: int = 10
):
    return {
        "resultado": analizar_inventario(
            limite_stock
        )
    }

@router.get("/oportunidades-oferta")
def test_oportunidades_oferta(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    limite_ventas: int = 2,
    stock_minimo: int = 1
):
    return {
        "resultado": analizar_oportunidades_oferta(
            fecha_inicio,
            fecha_fin,
            limite_ventas,
            stock_minimo
        )
    }