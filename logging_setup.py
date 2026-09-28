import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    CAMPOS = ("admin_id", "user_id", "conversation_id", "tools", "duration_ms", "error_type", "operation")

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage()
        }
        for campo in self.CAMPOS:
            valor = getattr(record, campo, None)
            if valor is not None:
                payload[campo] = valor
        if record.exc_info:
            payload["exception"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, default=str)


def get_logger(nombre: str):
    logger = logging.getLogger(nombre)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
