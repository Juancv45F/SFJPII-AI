from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str

    sfjpii_ai_service_key: str

    openai_api_key: str
    openai_model: str = "gpt-6-luna"
    chat_retention_days: int = Field(default=180, ge=0, le=3650)
    pharmacy_info_docx: str = "data/informacion_farmacia.docx"
    sfjpii_backend_url: str = "https://sfjpii-back.onrender.com"
    keep_alive_interval_seconds: int = Field(default=780, ge=60, le=86400)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
