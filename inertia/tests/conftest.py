from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from inertia.settings import settings
from inertia.test import ClientWithLastResponse


@pytest.fixture
def app():
    """Create a base FastAPI app for testing."""
    app = FastAPI()
    return app


@pytest.fixture
def client(app):
    """Create a regular TestClient fixture."""
    client = TestClient(app)
    return ClientWithLastResponse(client)


@pytest.fixture
def inertia_client(app):
    """Create an Inertia TestClient fixture."""
    client = TestClient(app)
    return ClientWithLastResponse(client, is_inertia=True)


@pytest.fixture
def render_mock():
    """Mock the render_to_string function for testing."""
    with patch("inertia.http.render_to_string") as mock:
        yield mock


@pytest.fixture
def templates():
    """Create Jinja2Templates for testing."""
    return Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@pytest.fixture
def csrf_token():
    """Generate a CSRF token for testing."""
    import secrets

    return secrets.token_hex(16)
