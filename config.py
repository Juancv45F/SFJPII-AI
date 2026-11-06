from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


AI_PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "api_key_field": "deepseek_api_key",
    },
    "qwen": {
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "api_key_field": "dashscope_api_key",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        # GPT-6.1 Terra/Sol y GPT-6 Astra exigen la Responses API para tools;
        # este servicio usa Chat Completions.
        "model": "gpt-6-luna",
        "api_key_field": "openai_api_key",
    },
}


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str

    sfjpii_ai_service_key: str

    ai_provider: Literal["deepseek", "qwen", "openai"] = "deepseek"
    # Vacíos usan los valores por defecto del proveedor elegido.
    ai_model: str = ""
    ai_base_url: str = ""
    deepseek_api_key: str = ""
    dashscope_api_key: str = ""
    openai_api_key: str = ""
    # Solo OpenAI. Con tools en Chat Completions debe ser "none"; "off" omite
    # el parámetro para modelos que no lo aceptan.
    ai_reasoning_effort: str = ""
    # Límites por llamada y por turno completo, por debajo del maxDuration de
    # 300 s de vercel.json. Si se cambian, revisa ambos valores juntos.
    ai_request_timeout_seconds: float = Field(default=45, gt=0)
    ai_turn_timeout_seconds: float = Field(default=225, gt=0)
    # Tope de tokens generados por llamada: acota el gasto de cada turno.
    ai_max_output_tokens: int = Field(default=2048, gt=0)
    chat_retention_days: int = Field(default=180, ge=0, le=3650)
    pharmacy_info_docx: str = "data/informacion_farmacia.docx"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Un .env con variables antiguas no debe impedir el arranque.
        extra="ignore",
        # Evita que un error de configuración imprima claves en los logs.
        hide_input_in_errors=True
    )

    @model_validator(mode="after")
    def resolver_proveedor_ai(self):
        proveedor = AI_PROVIDERS[self.ai_provider]
        self.ai_model = self.ai_model or proveedor["model"]
        self.ai_base_url = self.ai_base_url or proveedor["base_url"]
        self.ai_reasoning_effort = self.ai_reasoning_effort or "none"

        if not self.ai_api_key:
            variable = proveedor["api_key_field"].upper()
            raise ValueError(f"Falta {variable} para AI_PROVIDER={self.ai_provider}")

        return self

    @property
    def ai_api_key(self) -> str:
        return getattr(self, AI_PROVIDERS[self.ai_provider]["api_key_field"])


settings = Settings()
