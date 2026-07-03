import os


class Settings:
    cors_allow_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prospect_assist")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


settings = Settings()
