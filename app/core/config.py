"""Configuration settings for the appointment booking system."""

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str
    port: int
    user: str
    password: str
    database: str


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="allow"
    )
    
    # Application settings
    app_name: str = "Telegram Appointment Bot"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_database: str = "appointment_db"
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )
    
    # Neo4j settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}"
    
    # Telegram Bot settings
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = ""
    
    # LLM settings
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "openai"  # "openai" or "anthropic"
    llm_model: str = "gpt-4.1-nano"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    
    # Vector database settings
    vector_db_provider: str = "pinecone"  # "pinecone", "chroma", "weaviate"
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "appointment-bot"
    
    # Embedding settings
    embedding_provider: str = "openai"  # "openai" or "sentence-transformers"
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536
    
    # Business settings
    business_name: str = "Your Business"
    business_timezone: str = "UTC"
    default_appointment_duration: int = 60  # minutes
    booking_advance_days: int = 30
    cancellation_hours: int = 24
    
    # RAG settings
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7
    
    # Graph database settings
    graph_batch_size: int = 100
    graph_max_traversal_depth: int = 3
    recommendation_limit: int = 10
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Calendar integration
    google_calendar_credentials_file: str = "credentials.json"
    google_calendar_token_file: str = "token.json"
    
    # Celery settings
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    
    @property
    def celery_broker_url_computed(self) -> str:
        """Get Celery broker URL."""
        return self.celery_broker_url or self.redis_url
    
    @property
    def celery_result_backend_computed(self) -> str:
        """Get Celery result backend URL."""
        return self.celery_result_backend or self.redis_url


# Global settings instance
settings = Settings()


class AppConfig:
    """Application configuration."""
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".txt", ".docx", ".md"]
    
    # Conversation settings
    MAX_CONVERSATION_HISTORY: int = 20
    SESSION_TIMEOUT: int = 3600  # seconds
    
    # Function calling settings
    FUNCTION_TIMEOUT: int = 30  # seconds
    MAX_FUNCTION_CALLS: int = 10
    
    # Graph traversal settings
    MAX_GRAPH_DEPTH: int = 5
    MAX_GRAPH_NODES: int = 1000


app_config = AppConfig()