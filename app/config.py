# app/config.py
from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    host: str = "0.0.0.0"
    port: int = 8000
    environment: Literal["development", "production"] = "development"

    admin_secret: str = Field(..., description="Shared secret for admin endpoints")

    playwright_timeout_ms: int = 30000
    max_page_size_mb: int = 50
    max_images: int = 50
    image_download_timeout_s: int = 15
    max_image_size_mb: int = 10

    # Keep as raw strings for env var parsing
    allowed_domains: str = ""
    blocked_domains: str = ""

    log_level: str = "INFO"
    
    # Batch processing
    batch_max_urls: int = Field(default=50, description="Max URLs per batch request")
    batch_concurrency: int = Field(default=3, description="Max parallel browser instances")
    batch_timeout_per_url_s: int = Field(default=120, description="Timeout per URL in batch")

    # CORS Configuration
    cors_allow_origins: str = "*"  # Comma-separated origins, or "*" for all
    cors_allow_credentials: bool = False
    cors_allow_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allow_headers: str = "*,Authorization,Content-Type"
    cors_expose_headers: str = ""

    # Parse domains into sets for internal use
    @property
    def allowed_domains_set(self) -> set[str]:
        return {d.strip().lower() for d in self.allowed_domains.split(",") if d.strip()} if self.allowed_domains else set()

    @property
    def blocked_domains_set(self) -> set[str]:
        return {d.strip().lower() for d in self.blocked_domains.split(",") if d.strip()} if self.blocked_domains else set()

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_allow_origins_list(self) -> list[str] | Literal["*"]:
        """Parse CORS origins: '*' stays '*', otherwise split comma-separated list."""
        if self.cors_allow_origins.strip() == "*":
            return "*"
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return [m.strip().upper() for m in self.cors_allow_methods.split(",") if m.strip()]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        headers = [h.strip() for h in self.cors_allow_headers.split(",") if h.strip()]
        return ["*"] if "*" in headers else headers

    @property
    def cors_expose_headers_list(self) -> list[str]:
        return [h.strip() for h in self.cors_expose_headers.split(",") if h.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()