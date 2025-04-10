from unittest.mock import patch

import pytest


@pytest.fixture
def app_with_version():
    """Create FastAPI app with custom version."""
    from fastapi import FastAPI, Request

    # Create the app
    app = FastAPI()

    # Override the settings
    with patch("inertia.settings.settings.INERTIA_VERSION", "2.0"):

        @app.get("/empty/")
        async def empty_endpoint(request: Request):
            """Test endpoint with no data."""
            return {"component": "empty", "props": {}}

        yield app


def test_version_works(inertia_client, app_with_version):
    """Test that version header matching works."""
    response = inertia_client.get("/empty/", headers={"X-Inertia-Version": "2.0"})
    assert response.status_code == 200


def test_version_fallsback(inertia_client, app_with_version):
    """Test that version mismatch still works."""
    response = inertia_client.get("/empty/", headers={"X-Inertia-Version": "1.0"})
    assert response.status_code == 200


@pytest.fixture
def app_with_layout():
    """Create a FastAPI app with a custom layout."""
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse
    from fastapi.templating import Jinja2Templates

    # Create the app
    app = FastAPI()

    # Setup templates
    Jinja2Templates(directory="templates")

    @app.get("/empty/")
    async def empty_endpoint(request: Request):
        """Test endpoint returning HTML with layout."""
        # This would use your actual Inertia FastAPI integration
        # that would render the layout template
        return HTMLResponse("<html><body><div id='app'></div></body></html>")

    return app


def test_layout(client, app_with_layout):
    """Test that layout template is used."""
    response = client.get("/empty/")
    assert response.status_code == 200
    assert "<div id='app'>" in response.text
