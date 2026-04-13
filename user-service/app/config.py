from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/noteflow_users"

    redis_url: str = "redis://localhost:6379"

    kafka_bootstrap_servers: str = "localhost:9092"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    cookie_secure: bool = False  # True в продакшене (только HTTPS)

    log_level: str = "INFO"


settings = Settings()
