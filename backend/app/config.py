from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "portfolio_pilot"
    jwt_secret: str = "local-development-only-change-me"
    jwt_expire_minutes: int = 10080
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"
    max_upload_mb: int = 25
    frontend_origin: str = "http://localhost:5173"
    preview_base_url: str = "http://localhost:8001"
    public_api_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


settings = Settings()
