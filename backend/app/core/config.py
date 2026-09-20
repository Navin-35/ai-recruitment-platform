from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Recruitment & Candidate Matching Platform"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = "sqlite:///./recruitment.db"

    google_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()