from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    s3_endpoint: str = "localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "taste-media"
    embedding_model: str = "all-MiniLM-L6-v2"
    secret_key: str = "change-me"
    debug: bool = True
    tmdb_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
