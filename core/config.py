from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT
    SECRET_KEY: str = "Fetyvxfg5vtb@2636Tjdcui8n6cs7dd78dn8"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = ""
    DB: str = "" # Keep for backwards compat if needed

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
