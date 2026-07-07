import os
from pathlib import Path

# services/scoring-service/app/core/config.py -> repo root is 4 parents up
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_SYNTHETIC_DATA_DIR = _REPO_ROOT / "packages" / "synthetic-data-generator" / "data"


class Settings:
    cors_allow_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prospect_assist")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    synthetic_data_dir: str = os.getenv("SYNTHETIC_DATA_DIR", str(_DEFAULT_SYNTHETIC_DATA_DIR))


settings = Settings()
