import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
STATE_DIR = DATA_DIR / "state"

RAW_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ingestiq_db")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@dataclass(frozen=True)
class Paths:
    base_dir: Path = BASE_DIR
    data_dir: Path = DATA_DIR
    raw_dir: Path = RAW_DIR
    state_dir: Path = STATE_DIR


@dataclass(frozen=True)
class ApiSettings:
    timeout_s: float = 15.0
    max_retries: int = 3
    backoff_min_s: float = 0.5
    backoff_max_s: float = 5.0


@dataclass(frozen=True)
class Settings:
    db_user: str = DB_USER
    db_password: str = DB_PASSWORD
    db_host: str = DB_HOST
    db_port: str = DB_PORT
    db_name: str = DB_NAME
    database_url: str = DATABASE_URL
    paths: Paths = Paths()
    api: ApiSettings = ApiSettings()
    OPENAI_API_KEY: str = OPENAI_API_KEY


app_settings = Settings()
