from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "noteflow_notes"

    redis_url: str = "redis://localhost:6379"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "note-service"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    rate_limit_enabled: bool = True

    log_level: str = "INFO"


settings = Settings()
