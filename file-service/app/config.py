from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/noteflow_files"

    redis_url: str = "redis://localhost:6379"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "file-service"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_use_ssl: bool = False
    minio_bucket_hot: str = "noteflow-hot"
    minio_bucket_warm: str = "noteflow-warm"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    max_upload_size: int = 100 * 1024 * 1024  # 100 MB

    rate_limit_enabled: bool = True

    log_level: str = "INFO"


settings = Settings()
