"""
Inertia.js integration for FastAPI.

This package provides a FastAPI integration for Inertia.js,
enabling server-driven single-page applications.
"""

from .http import (
    InertiaResponse,
    create_inertia,
    inertia,
    location,
    render,
    setup_inertia,
)
from .middleware import InertiaMiddleware, setup_inertia_middleware
from .share import share
from .utils import defer, lazy, merge, optional

__all__ = [
    # Core components
    "InertiaResponse",
    "inertia",
    "location",
    "render",
    # FastAPI integration
    "setup_inertia",
    "create_inertia",
    "InertiaMiddleware",
    "setup_inertia_middleware",
    # Data handling
    "share",
    # Prop utilities
    "defer",
    "lazy",
    "merge",
    "optional",
]
