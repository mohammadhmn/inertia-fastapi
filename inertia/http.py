"""
Inertia.js integration for FastAPI.

This module provides the necessary classes and functions to integrate
Inertia.js with FastAPI applications, enabling server-driven single-page applications.
"""

from functools import wraps
from http import HTTPStatus
from json import dumps as json_encode
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .helpers import deep_transform_callables, validate_type
from .prop_classes import DeferredProp, IgnoreOnFirstLoadProp, MergeableProp
from .settings import get_settings

# Constants
INERTIA_REQUEST_ENCRYPT_HISTORY = "_inertia_encrypt_history"
INERTIA_SESSION_CLEAR_HISTORY = "_inertia_clear_history"
TEMPLATES_DIR = "templates"  # Default templates directory


class InertiaRequest:
    """Wrapper for FastAPI Request to handle Inertia-specific properties.

    This class wraps a FastAPI Request object and adds Inertia-specific functionality
    such as handling partial reloads, shared data, and history encryption.
    """

    def __init__(self, request: Request):
        """Initialize the InertiaRequest.

        Args:
            request: The original FastAPI request
        """
        self.request = request
        self._inertia_state: Dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped request."""
        return getattr(self.request, name)

    @property
    def headers(self) -> Dict[str, str]:
        """Get all headers as a dictionary."""
        return dict(self.request.headers)

    @property
    def inertia(self) -> Dict[str, Any]:
        """Get shared Inertia data."""
        # First check for data in request.state.inertia (new approach)
        if hasattr(self.request.state, "inertia"):
            return self.request.state.inertia.all()
        # Fall back to _inertia_state (our internal storage)
        return self._inertia_state

    def set_inertia_state(self, data: Dict[str, Any]) -> None:
        """Set shared data that will be included with all Inertia responses."""
        # Store data in both places for backward compatibility
        self._inertia_state = data

        # Also store in request.state.inertia if it exists
        if hasattr(self.request.state, "inertia"):
            self.request.state.inertia.set(**data)
        else:
            # Create InertiaShare instance in request.state
            from .share import InertiaShare

            self.request.state.inertia = InertiaShare()
            self.request.state.inertia.set(**data)

    def is_inertia(self) -> bool:
        """Check if this is an Inertia request."""
        return "X-Inertia" in self.headers

    def is_a_partial_render(self, component: str) -> bool:
        """Check if this is a partial render for a specific component."""
        return (
            "X-Inertia-Partial-Data" in self.headers
            and self.headers.get("X-Inertia-Partial-Component", "") == component
        )

    def partial_keys(self) -> List[str]:
        """Get the partial keys requested in the partial render."""
        return self.headers.get("X-Inertia-Partial-Data", "").split(",")

    def reset_keys(self) -> List[str]:
        """Get the keys that should be reset (not merged)."""
        return self.headers.get("X-Inertia-Reset", "").split(",")

    def should_encrypt_history(self) -> bool:
        """Check if history should be encrypted for this request."""
        settings = get_settings()
        encrypt_history = getattr(
            self.request.state,
            INERTIA_REQUEST_ENCRYPT_HISTORY,
            settings.INERTIA_ENCRYPT_HISTORY,
        )
        return validate_type(
            encrypt_history,
            expected_type=bool,
            name="encrypt_history",
        )


class InertiaResponse:
    """Inertia response for FastAPI.

    This class handles rendering Inertia responses, including support for
    SSR, partial reloads, and initial page loads.
    """

    def __init__(
        self,
        request: Request,
        component: str,
        props: Optional[Dict[str, Any]] = None,
        template_data: Optional[Dict[str, Any]] = None,
        status_code: int = HTTPStatus.OK,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize the InertiaResponse.

        Args:
            request: The FastAPI request
            component: The Inertia component to render
            props: The props to pass to the component
            template_data: Additional data for the template
            status_code: HTTP status code
            headers: Additional HTTP headers
        """
        self.inertia_request = InertiaRequest(request)
        self.component = component
        self.props = props or {}
        self.template_data = template_data or {}
        self.status_code = status_code
        self.headers = headers or {}
        self.templates = Jinja2Templates(directory=TEMPLATES_DIR)

    async def __call__(self) -> Union[HTMLResponse, JSONResponse]:
        """Return the appropriate response when called.

        Returns:
            JSONResponse for Inertia requests, HTMLResponse for initial page loads
        """
        # Build the page data
        page_data = self._build_page_data()

        # Encode to JSON
        settings = get_settings()
        data = json_encode(page_data, cls=settings.INERTIA_JSON_ENCODER)

        if self.inertia_request.is_inertia():
            # Handle Inertia XHR request
            headers = {
                **self.headers,
                "Vary": "X-Inertia",
                "X-Inertia": "true",
                "Content-Type": "application/json",
            }
            return JSONResponse(
                content=data,
                status_code=self.status_code,
                headers=headers,
            )
        else:
            # Handle initial page load
            content = await self._build_first_load(data)
            return HTMLResponse(
                content=content,
                status_code=self.status_code,
                headers=self.headers,
            )

    def _build_page_data(self) -> Dict[str, Any]:
        """Build the page data for the Inertia response.

        Returns:
            Dictionary with component, props, URL, version, etc.
        """
        settings = get_settings()
        session = {}  # FastAPI doesn't have built-in sessions, use your session mechanism

        # Adapt this to your session mechanism
        clear_history = validate_type(
            session.pop(INERTIA_SESSION_CLEAR_HISTORY, False),
            expected_type=bool,
            name="clear_history",
        )

        _page = {
            "component": self.component,
            "props": self._build_props(),
            "url": str(self.inertia_request.url),
            "version": settings.INERTIA_VERSION,
            "encryptHistory": self.inertia_request.should_encrypt_history(),
            "clearHistory": clear_history,
        }

        _deferred_props = self._build_deferred_props()
        if _deferred_props:
            _page["deferredProps"] = _deferred_props

        _merge_props = self._build_merge_props()
        if _merge_props:
            _page["mergeProps"] = _merge_props

        return _page

    def _build_props(self) -> Dict[str, Any]:
        """Build props with partial rendering support.

        Returns:
            Dictionary of rendered props
        """
        _props = {
            **self.inertia_request.inertia,
            **self.props,
        }

        for key in list(_props.keys()):
            if self.inertia_request.is_a_partial_render(self.component):
                # For partial reloads, only include requested props
                if key not in self.inertia_request.partial_keys():
                    del _props[key]
            else:
                # For first load, remove props marked to be ignored on first load
                if isinstance(_props[key], IgnoreOnFirstLoadProp):
                    del _props[key]

        return deep_transform_callables(_props)

    def _build_deferred_props(self) -> Optional[Dict[str, List[str]]]:
        """Build deferred props for lazy loading.

        Returns:
            Dictionary of deferred prop groups or None if no deferred props
        """
        if self.inertia_request.is_a_partial_render(self.component):
            return None

        _deferred_props = {}
        for key, prop in self.props.items():
            if isinstance(prop, DeferredProp):
                _deferred_props.setdefault(prop.group, []).append(key)

        return _deferred_props if _deferred_props else None

    def _build_merge_props(self) -> List[str]:
        """Build mergeable props list.

        Returns:
            List of prop names that should be merged rather than replaced
        """
        return [
            key
            for key, prop in self.props.items()
            if (
                isinstance(prop, MergeableProp)
                and prop.should_merge()
                and key not in self.inertia_request.reset_keys()
            )
        ]

    async def _build_first_load(self, data: str) -> str:
        """Build HTML for first load.

        Args:
            data: JSON-encoded page data

        Returns:
            HTML string for the initial page load
        """
        context, template_name = await self._build_first_load_context_and_template(data)
        settings = get_settings()

        # Render template with Jinja2
        return self.templates.get_template(template_name).render(
            inertia_layout=settings.INERTIA_LAYOUT, **context
        )

    async def _build_first_load_context_and_template(
        self, data: str
    ) -> Tuple[Dict[str, Any], str]:
        """Build context and template for first load.

        Args:
            data: JSON-encoded page data

        Returns:
            Tuple of (context dict, template name)
        """
        settings = get_settings()

        # Try SSR if enabled
        if settings.INERTIA_SSR_ENABLED:
            try:
                response = requests.post(
                    f"{settings.INERTIA_SSR_URL}/render",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return {
                    **response.json(),
                    **self.template_data,
                }, "inertia_ssr.html"
            except Exception:
                # Fall back to client-side rendering if SSR fails
                pass

        return {
            "page": data,
            **self.template_data,
        }, "inertia.html"


# Public API functions


async def render(
    request: Request,
    component: str,
    props: Optional[Dict[str, Any]] = None,
    template_data: Optional[Dict[str, Any]] = None,
    status_code: int = HTTPStatus.OK,
) -> Union[HTMLResponse, JSONResponse]:
    """Render an Inertia response.

    This is the main function for rendering Inertia responses when not using decorators.

    Args:
        request: The FastAPI request
        component: The Inertia component to render
        props: The props to pass to the component
        template_data: Additional data for the template
        status_code: HTTP status code

    Returns:
        An Inertia response (either HTML or JSON)
    """
    response = InertiaResponse(
        request,
        component,
        props or {},
        template_data or {},
        status_code,
    )
    return await response()


def location(url: str) -> Response:
    """Create a location response for redirects.

    This is used for external redirects from Inertia.

    Args:
        url: The URL to redirect to

    Returns:
        A response that will trigger a client-side redirect
    """
    return Response(
        content="",
        status_code=HTTPStatus.CONFLICT,
        headers={"X-Inertia-Location": url},
    )


def encrypt_history(request: Request, value: bool = True) -> None:
    """Set encrypt history flag on request state.

    Args:
        request: The FastAPI request
        value: Whether to encrypt history (default: True)
    """
    setattr(request.state, INERTIA_REQUEST_ENCRYPT_HISTORY, value)


def clear_history(request: Request) -> None:
    """Set clear history flag in session.

    Args:
        request: The FastAPI request
    """
    # Adapt this to your session mechanism
    pass


def inertia(component: str) -> Callable:
    """Decorator for Inertia page handlers.

    This decorator transforms the return value of a handler function
    into an Inertia response with the specified component.

    Args:
        component: The Inertia component to render

    Returns:
        A decorator function that wraps the route handler

    Example:
        @app.get("/dashboard")
        @inertia("Dashboard")
        async def dashboard(request: Request):
            return {
                "title": "Dashboard",
                "stats": get_stats()
            }
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def inner(request: Request, *args, **kwargs) -> Any:
            props = await func(request, *args, **kwargs)

            # If something other than a dict is returned, pass it through
            if not isinstance(props, dict):
                return props

            return await render(request, component, props)

        return inner

    return decorator


class InertiaRouteBuilder:
    """Provides method-specific decorators for Inertia routes.

    This class offers a fluent API for defining Inertia routes, similar to
    FastAPI's own route decorators but with built-in Inertia support.

    Example:
        app = FastAPI()
        inertia = InertiaRouteBuilder(app)

        @inertia.get("/", "Home")
        async def home(request: Request):
            return {"title": "Home"}
    """

    def __init__(self, app: FastAPI):
        """Initialize the InertiaRouteBuilder.

        Args:
            app: The FastAPI application
        """
        self.app = app

    def _route(
        self, path: str, component: str, methods: List[str], **kwargs
    ) -> Callable:
        """Internal method to create a route with specific methods.

        Args:
            path: The route path
            component: The Inertia component to render
            methods: HTTP methods to register
            **kwargs: Additional arguments for the FastAPI route

        Returns:
            A decorator function
        """

        def decorator(func: Callable) -> Callable:
            # First apply the Inertia decorator
            inertia_func = inertia(component)(func)

            # Then register the route with FastAPI for each method
            method_map = {
                "get": self.app.get,
                "post": self.app.post,
                "put": self.app.put,
                "delete": self.app.delete,
                "patch": self.app.patch,
                "head": self.app.head,
                "options": self.app.options,
            }

            for method in methods:
                method = method.lower()
                if method in method_map:
                    method_map[method](path, **kwargs)(inertia_func)

            # Return the original function for middleware stacking
            return func

        return decorator

    def get(self, path: str, component: str, **kwargs) -> Callable:
        """Register a GET route with Inertia.

        Args:
            path: The route path
            component: The Inertia component to render
            **kwargs: Additional arguments for the FastAPI route

        Returns:
            A decorator function
        """
        return self._route(path, component, ["GET"], **kwargs)

    def post(self, path: str, component: str, **kwargs) -> Callable:
        """Register a POST route with Inertia."""
        return self._route(path, component, ["POST"], **kwargs)

    def put(self, path: str, component: str, **kwargs) -> Callable:
        """Register a PUT route with Inertia."""
        return self._route(path, component, ["PUT"], **kwargs)

    def delete(self, path: str, component: str, **kwargs) -> Callable:
        """Register a DELETE route with Inertia."""
        return self._route(path, component, ["DELETE"], **kwargs)

    def patch(self, path: str, component: str, **kwargs) -> Callable:
        """Register a PATCH route with Inertia."""
        return self._route(path, component, ["PATCH"], **kwargs)

    def route(
        self,
        path: str,
        component: str,
        methods: Optional[List[str]] = None,
        **kwargs,
    ) -> Callable:
        if methods is None:
            methods = ["GET"]
        """Register a route with multiple methods with Inertia.

        Args:
            path: The route path
            component: The Inertia component to render
            methods: List of HTTP methods to register
            **kwargs: Additional arguments for the FastAPI route

        Returns:
            A decorator function
        """
        return self._route(path, component, methods, **kwargs)


def create_inertia(app: FastAPI) -> InertiaRouteBuilder:
    """Create an Inertia instance for the given FastAPI app.

    Args:
        app: The FastAPI application

    Returns:
        An InertiaRouteBuilder instance
    """
    return InertiaRouteBuilder(app)


def setup_inertia(
    app: FastAPI,
    templates_dir: str = "templates",
    shared_data_callback: Optional[Callable[[Request], Dict[str, Any]]] = None,
) -> InertiaRouteBuilder:
    """Setup Inertia for a FastAPI app and return an inertia instance.

    This function sets up the Inertia middleware and returns an InertiaRouteBuilder
    instance for creating routes.

    Args:
        app: The FastAPI application
        templates_dir: Directory containing Jinja2 templates
        shared_data_callback: Function to provide shared data for all Inertia requests

    Returns:
        An InertiaRouteBuilder instance for creating routes

    Example:
        app = FastAPI()
        inertia = setup_inertia(
            app=app,
            templates_dir="templates",
            shared_data_callback=lambda req: {"user": req.state.user}
        )

        @inertia.get("/dashboard", "Dashboard")
        async def dashboard(request: Request):
            return {"stats": get_stats()}
    """
    from .middleware import setup_inertia_middleware

    global TEMPLATES_DIR
    TEMPLATES_DIR = templates_dir

    # Setup Inertia middleware
    setup_inertia_middleware(app)

    # Setup shared data middleware
    if shared_data_callback:

        @app.middleware("http")
        async def shared_data_middleware(
            request: Request, call_next: Callable
        ) -> Response:
            """Middleware to handle Inertia shared data."""
            inertia_request = InertiaRequest(request)
            shared_data = shared_data_callback(request)
            inertia_request.set_inertia_state(shared_data)
            return await call_next(request)

    # Return an inertia instance
    return create_inertia(app)
