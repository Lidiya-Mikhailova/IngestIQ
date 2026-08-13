import pytest
from pathlib import Path
from src.config.settings import BASE_DIR, RAW_DIR, DATABASE_URL

def test_base_dir():
    assert isinstance(BASE_DIR, Path)
    assert BASE_DIR.name == "IngestIQ"

def test_raw_dir():
    assert isinstance(RAW_DIR, Path)
    assert "raw" in str(RAW_DIR)

def test_database_url():
    assert DATABASE_URL.startswith("postgresql://")

def test_settings_exists():
    assert BASE_DIR is not None
    assert RAW_DIR is not None
    assert DATABASE_URL is not None
