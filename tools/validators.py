from datetime import datetime, timezone


class ToolValidationError(ValueError):
    pass


def fecha_iso(valor, nombre: str) -> datetime:
    if isinstance(valor, datetime):
        fecha = valor
    elif isinstance(valor, str):
        try:
            fecha = datetime.fromisoformat(valor.strip().replace("Z", "+00:00"))
        except ValueError as error:
            raise ToolValidationError(f"{nombre} debe ser una fecha ISO 8601 válida") from error
    else:
        raise ToolValidationError(f"{nombre} debe ser una fecha ISO 8601 válida")
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def rango(argumentos: dict, inicio: str = "fecha_inicio", fin: str = "fecha_fin"):
    fecha_inicio = fecha_iso(argumentos.get(inicio), inicio)
    fecha_fin = fecha_iso(argumentos.get(fin), fin)
    if fecha_inicio > fecha_fin:
        raise ToolValidationError(f"{inicio} no puede ser posterior a {fin}")
    return fecha_inicio, fecha_fin


def entero_limite(valor, nombre: str, minimo: int, maximo: int) -> int:
    if isinstance(valor, bool):
        raise ToolValidationError(f"{nombre} debe ser un número entero")
    try:
        numero = int(valor)
    except (TypeError, ValueError) as error:
        raise ToolValidationError(f"{nombre} debe ser un número entero") from error
    if not isinstance(valor, int) and str(valor).strip() not in {str(numero), f"+{numero}"}:
        raise ToolValidationError(f"{nombre} debe ser un número entero")
    if numero < minimo or numero > maximo:
        raise ToolValidationError(f"{nombre} debe estar entre {minimo} y {maximo}")
    return numero
