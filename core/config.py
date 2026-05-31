from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "Cloud Clipboard API"
    APP_VERSION: str = "1.0.0"

    # JWT
    SECRET_KEY: str = "Fetyvxfg5vtb@2636Tjdcui8n6cs7dd78dn8"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = ""
    DB: str = ""  # Keep for backwards compat if needed

    # Redis (optional — falls back to in-memory if not set)
    REDIS_URL: str = ""

    # CORS — comma-separated origins
    CORS_ORIGINS: str = "*"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10

    # Rate limiting (requests per minute for auth endpoints)
    RATE_LIMIT_AUTH_RPM: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
