from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Recruitment & Candidate Intelligence Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    database_url: str = "sqlite:///./recruitment.db"

    google_api_key: str = ""
    gemini_model_text: str = "gemini-1.5-flash"
    gemini_model_embedding: str = "gemini-embedding-001"

    # Supabase Configuration
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Storage Buckets
    storage_bucket_resumes: str = "resumes"
    storage_bucket_jobs: str = "job-descriptions"
    storage_bucket_exports: str = "exports"
    storage_signed_url_expiry: int = 3600  # 1 hour

    # Security & Auth Settings
    enable_auth_enforcement: bool = False
    default_tenant_id: str = "tenant-enterprise-01"

    # Redis Async Background Queue
    redis_url: str = "redis://localhost:6379/0"
    enable_redis_queue: bool = False

    # Observability (Langfuse)
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    enable_langfuse: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()