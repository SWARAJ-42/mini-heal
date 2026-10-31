"""Shared runtime settings loaded from the project .env or environment."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

APP_NAME = os.getenv("APP_NAME", "MiniHeal")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "miniheal-api")
HEALTH_URL = os.getenv("HEALTH_URL", "http://localhost:8000/health")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./miniheal.db")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-6-astra")

# Environment values are strings; use 1 to enable the failure simulation.
SIMULATE_DB_FAILURE = os.getenv("MINIHEAL_SIMULATE_DB_FAILURE", "0") == "1"
