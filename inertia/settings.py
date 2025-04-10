from functools import lru_cache
from typing import Type

from pydantic import BaseSettings

from .utils import InertiaJsonEncoder

__all__ = ["get_settings"]


class InertiaSettings(BaseSettings):
    """Inertia settings for FastAPI"""

    INERTIA_VERSION: str = "1.0"
    INERTIA_JSON_ENCODER: Type = InertiaJsonEncoder
    INERTIA_SSR_URL: str = "http://localhost:13714"
    INERTIA_SSR_ENABLED: bool = False
    INERTIA_ENCRYPT_HISTORY: bool = False
    INERTIA_LAYOUT: str = "base.html"

    class Config:
        env_prefix = "INERTIA_"


@lru_cache()
def get_settings() -> InertiaSettings:
    """Get cached settings instance"""
    return InertiaSettings()
