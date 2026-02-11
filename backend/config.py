import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(PROJECT_ROOT / "resume_matcher.db")


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("RESUME_MATCHER_DB_PATH", DEFAULT_DB_PATH)
    lm_base_url: str = os.getenv("RESUME_MATCHER_LM_BASE_URL", "http://127.0.0.1:1234/v1")
    lm_api_key: str = os.getenv("RESUME_MATCHER_LM_API_KEY", "lm-studio")


settings = Settings()
