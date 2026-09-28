from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )

    conversation_id: Optional[str] = None


class GraficaResponse(BaseModel):
    tipo: str
    titulo: str
    labels: list[str]
    data: list[float]


class ChatResponse(BaseModel):
    respuesta: str
    tools_utilizadas: list[str] = []
    grafica: Optional[GraficaResponse] = None
    conversation_id: str