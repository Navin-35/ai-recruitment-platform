from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Recruitment & Candidate Matching Platform"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = "sqlite:///./recruitment.db"

    google_api_key: str = ""

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()