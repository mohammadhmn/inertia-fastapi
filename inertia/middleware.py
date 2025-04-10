"""
Inertia.js middleware for FastAPI.

This module provides middleware for handling Inertia.js protocol requirements
such as version checking, redirects, and other Inertia-specific behaviors.
"""

from http import HTTPStatus
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .http import location
from .settings import get_settings


class InertiaMiddleware(BaseHTTPMiddleware):
    """Middleware for handling Inertia.js protocol requirements.

    This middleware handles:
    - Version checking to force refreshes when assets change
    - Converting certain redirects to 303 responses for non-GET methods
    - Handling Inertia redirects properly
    - Other Inertia-specific behaviors
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through middleware.

        Args:
            request: The incoming request
            call_next: Function to call the next middleware/route handler

        Returns:
            The response
        """
        # Check for stale Inertia version on GET requests
        if (
            self._is_inertia_request(request)
            and request.method == "GET"
            and self._is_stale(request)
        ):
            return self._force_refresh(request)

        # Process the request through the rest of the app
        response = await call_next(request)

        # Handle Inertia requests
        if self._is_inertia_request(request):
            # Convert non-GET redirects to 303 See Other
            if self._is_non_get_redirect(request, response):
                response.status_code = HTTPStatus.SEE_OTHER  # 303 See Other

            # Handle regular redirects for Inertia requests
            elif self._is_redirect_response(response):
                # Convert to Inertia location response
                location_url = response.headers.get("Location", "/")
                response.status_code = HTTPStatus.CONFLICT
                response.headers["X-Inertia-Location"] = location_url
                # Clear the original location header to avoid conflicts
                if "Location" in response.headers:
                    del response.headers["Location"]

        return response

    def _is_inertia_request(self, request: Request) -> bool:
        """Check if this is an Inertia request."""
        return "X-Inertia" in request.headers

    def _is_redirect_response(self, response: Response) -> bool:
        """Check if this is a redirect response."""
        return response.status_code in [
            HTTPStatus.MOVED_PERMANENTLY,
            HTTPStatus.FOUND,
        ]  # 301, 302

    def _is_non_get_redirect(self, request: Request, response: Response) -> bool:
        """Check if this is a non-GET redirect that should be converted to 303."""
        return self._is_redirect_response(response) and request.method in [
            "PUT",
            "PATCH",
            "DELETE",
        ]

    def _is_stale(self, request: Request) -> bool:
        """Check if the Inertia version is stale."""
        settings = get_settings()
        return request.headers.get("X-Inertia-Version", "") != settings.INERTIA_VERSION

    def _force_refresh(self, request: Request) -> Response:
        """Force a refresh by returning a location response."""
        return location(str(request.url))


def setup_inertia_middleware(app: FastAPI) -> None:
    """Add the Inertia middleware to a FastAPI application.

    Args:
        app: The FastAPI application
    """
    app.add_middleware(InertiaMiddleware)
