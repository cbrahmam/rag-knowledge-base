"""Central application configuration.

Values are read from environment variables (with sensible defaults) so the
same code runs in local, CI and production without edits. Importing this
module also loads a .env file, so services work even when the app isn't
started through main.py (e.g. in tests or scripts).
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# --- App ---
VERSION: str = os.getenv("APP_VERSION", "1.0.0")

# --- Anthropic / generation ---
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6-20250514")
MAX_TOKENS: int = _int("ANTHROPIC_MAX_TOKENS", 1024)

# --- Retrieval ---
SIMILARITY_THRESHOLD: float = _float("SIMILARITY_THRESHOLD", 0.3)
DEFAULT_N_RESULTS: int = _int("DEFAULT_N_RESULTS", 5)
MAX_N_RESULTS: int = _int("MAX_N_RESULTS", 20)

# --- Uploads / chunking ---
MAX_FILE_SIZE: int = _int("MAX_FILE_SIZE", 10 * 1024 * 1024)
MAX_SUMMARY_CONTEXT_CHARS: int = _int("MAX_SUMMARY_CONTEXT_CHARS", 12000)

# --- HTTP / CORS ---
# Comma-separated list of allowed origins.
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
