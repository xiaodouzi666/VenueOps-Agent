from functools import cached_property
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_uri: str | None = Field(default=None, alias="MONGODB_URI")
    mongodb_db: str = Field(default="venueops_demo", alias="MONGODB_DB")
    mdb_mcp_connection_string: str | None = Field(default=None, alias="MDB_MCP_CONNECTION_STRING")
    use_real_mcp: bool = Field(default=False, alias="VENUEOPS_USE_REAL_MCP")
    allowed_db: str = Field(default="venueops_demo", alias="VENUEOPS_ALLOWED_DB")
    demo_mode: bool = Field(default=True, alias="VENUEOPS_DEMO_MODE")
    max_query_limit: int = Field(default=100, alias="VENUEOPS_MAX_QUERY_LIMIT")

    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="us-central1", alias="GOOGLE_CLOUD_LOCATION")
    google_genai_use_vertexai: bool = Field(default=True, alias="GOOGLE_GENAI_USE_VERTEXAI")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    @cached_property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
