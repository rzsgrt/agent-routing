"""Configuration management for the AI Agent Backend."""

import os


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


# FastAPI settings
APP_NAME = os.getenv("APP_NAME", "AI Agent Backend")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = get_env_bool("DEBUG", False)

# LM Studio settings
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY", "lm-studio")

# Weather API settings
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# Default location when no location specified
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "Jakarta")

# Agent settings
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "30"))
