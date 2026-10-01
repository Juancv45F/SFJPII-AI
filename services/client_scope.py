import re
import unicodedata


PHARMACY_TERMS = {
    "farmacia", "medicamento", "medicina", "producto", "catalogo",
    "precio", "cuesta", "costo", "stock", "existencia", "disponible",
    "agotado", "oferta", "descuento", "receta", "dosis", "dolor",
    "sintoma", "pedido", "pedidos", "encargo", "encargos", "entrega",
    "cancelar", "compra", "carrito", "horario", "abren", "cierran",
    "telefono", "contacto", "whatsapp", "direccion", "ubicacion",
    "sucursal", "tienen", "venden", "buscar", "busca", "comprar"
}

OFF_TOPIC_TERMS = {
    "internet", "navegador", "browser", "programacion", "programar",
    "codigo fuente", "python", "javascript", "historia universal",
    "politica", "futbol", "videojuego", "pelicula", "musica",
    "algebra", "ecuacion", "derivada", "integral", "raiz cuadrada"
}

CONVERSATION_TERMS = {
    "hola", "buenos dias", "buenas tardes", "buenas noches", "gracias",
    "si", "no", "de acuerdo", "adios"
}


def _normalizar(texto: str) -> str:
    value = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(char for char in value if unicodedata.category(char) != "Mn").strip()


def es_consulta_permitida(mensaje: str, historial: list[dict] | None = None) -> bool:
    texto = _normalizar(mensaje)
    if not texto:
        return False

    tiene_contexto_farmacia = any(term in texto for term in PHARMACY_TERMS)
    if not tiene_contexto_farmacia:
        if any(term in texto for term in OFF_TOPIC_TERMS):
            return False
        if re.search(r"(?:cuanto\s+(?:es|da)|calcula|resuelve|suma|resta|multiplica|divide)", texto):
            return False
        if re.fullmatch(r"[\d\s+*/=().,%^-]+", texto):
            return False

    if tiene_contexto_farmacia:
        return True
    if texto in CONVERSATION_TERMS:
        return True

    # Permite continuaciones breves como "¿y el segundo?" o "¿cuánto cuesta?"
    # únicamente cuando ya existe una conversación del cliente.
    if historial and len(texto) <= 100:
        referencias = ("ese", "esa", "esos", "esas", "primero", "segundo", "anterior", "y ", "cual", "cuando")
        if any(ref in texto for ref in referencias):
            return True

    return False


RESPUESTA_FUERA_DE_ALCANCE = (
    "Puedo ayudarte únicamente con asuntos de la Farmacia Juan Pablo II: "
    "productos, precios, disponibilidad, pedidos, encargos, horarios, "
    "ubicación y medios de contacto."
)
