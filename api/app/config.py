from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_port: int = 8000
    log_level: str = "INFO"

    redis_host: str = "redis"
    redis_port: int = 6379
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    model_name: str = "blanchefort/rubert-base-cased-sentiment"
    model_cache_dir: str = "/models"
    max_text_length: int = 512
    use_onnx: bool = False

    database_url: str = "postgresql+asyncpg://sentiment:sentiment@postgres:5432/sentiment"

    api_url: str = "http://nginx/api"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
