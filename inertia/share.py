"""
Inertia.js shared data handling for FastAPI.

This module provides a way to share data across all Inertia responses.
"""

from typing import Any, Dict

from fastapi import Request

__all__ = ["share"]


class InertiaShare:
    """Class to store and manage shared data across all Inertia responses."""

    def __init__(self):
        """Initialize with empty props dictionary."""
        self.props = {}

    def set(self, **kwargs: Any) -> None:
        """Add new shared data, merging with existing data.

        Args:
            **kwargs: Key-value pairs to share
        """
        self.props = {
            **self.props,
            **kwargs,
        }

    def all(self) -> Dict[str, Any]:
        """Get all shared data.

        Returns:
            Dictionary of all shared properties
        """
        return self.props


def share(request: Request, **kwargs: Any) -> None:
    """Share data across all Inertia responses for the current request.

    This function stores data in the request state that will be accessible
    to all Inertia responses for the current request.

    Args:
        request: The FastAPI request
        **kwargs: Key-value pairs to share

    Example:
        @app.get("/dashboard")
        @inertia("Dashboard")
        async def dashboard(request: Request):
            # Share user data with all Inertia responses
            share(request, user=current_user)
            return {"stats": get_stats()}
    """
    # Store inertia share object in request state
    if not hasattr(request.state, "inertia"):
        request.state.inertia = InertiaShare()

    request.state.inertia.set(**kwargs)

    # For backward compatibility with InertiaRequest
    # which uses _inertia_state instead of request.state.inertia
    if hasattr(request, "_inertia_state"):
        request._inertia_state = {
            **request._inertia_state,
            **kwargs,
        }
