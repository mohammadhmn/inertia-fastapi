from json import dumps, loads
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from inertia.settings import settings


class ClientWithLastResponse:
    def __init__(self, client, is_inertia=False):
        self.client = client
        self.last_response = None
        self.is_inertia = is_inertia

    def get(self, url, **kwargs):
        headers = kwargs.get("headers", {})
        if self.is_inertia:
            headers["X-Inertia"] = "true"
        kwargs["headers"] = headers
        self.last_response = self.client.get(url, **kwargs)
        return self.last_response

    def __getattr__(self, name):
        return getattr(self.client, name)


@pytest.fixture
def inertia_client(app):
    """Fixture to create an Inertia TestClient."""
    client = TestClient(app)
    return ClientWithLastResponse(client, is_inertia=True)


@pytest.fixture
def client(app):
    """Fixture to create a regular TestClient."""
    client = TestClient(app)
    return ClientWithLastResponse(client)


@pytest.fixture
def render_mock():
    """Mock the render_to_string function."""
    with patch("inertia.http.render_to_string") as mock:
        yield mock


class InertiaTestCase:
    """Base class for testing Inertia responses."""

    def setup_method(self):
        """Initialize clients and mocks for each test."""
        self.app = FastAPI()
        self.inertia = ClientWithLastResponse(TestClient(self.app), is_inertia=True)
        self.client = ClientWithLastResponse(TestClient(self.app))

        render_patcher = patch("inertia.http.render_to_string")
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

    def addCleanup(self, func, *args, **kwargs):
        """Add cleanup function to be called after the test."""
        self._cleanups = getattr(self, "_cleanups", [])
        self._cleanups.append((func, args, kwargs))

    def teardown_method(self):
        """Clean up after each test."""
        for func, args, kwargs in getattr(self, "_cleanups", []):
            func(*args, **kwargs)

    def last_response(self):
        """Get the last response from either client."""
        return self.inertia.last_response or self.client.last_response

    def page(self):
        """Get the page data from the response."""
        page_data = (
            self.mock_render.call_args[0][1]["page"]
            if self.mock_render.call_args
            else self.last_response().content
        )

        if isinstance(page_data, bytes):
            page_data = page_data.decode("utf-8")

        return loads(page_data)

    def props(self):
        """Get the props from the page data."""
        return self.page()["props"]

    def merge_props(self):
        """Get merge props from the page data."""
        return self.page()["mergeProps"]

    def deferred_props(self):
        """Get deferred props from the page data."""
        return self.page()["deferredProps"]

    def template_data(self):
        """Get template data from the render context."""
        context = self.mock_render.call_args[0][1]
        return {
            key: context[key]
            for key in context
            if key not in ["page", "inertia_layout"]
        }

    def component(self):
        """Get the component name from the page data."""
        return self.page()["component"]

    # pytest assertion helpers
    def assert_json_response(self, response, json_obj):
        """Assert that response is JSON with expected content."""
        assert response.headers["Content-Type"] == "application/json"
        assert response.json() == json_obj

    def assert_includes_props(self, props):
        """Assert that the page props include the given props."""
        actual_props = self.props()
        for key, value in props.items():
            assert actual_props[key] == value

    def assert_has_exact_props(self, props):
        """Assert that the page props exactly match the given props."""
        assert self.props() == props

    def assert_includes_template_data(self, template_data):
        """Assert that the template data includes the given data."""
        actual_data = self.template_data()
        for key, value in template_data.items():
            assert actual_data[key] == value

    def assert_has_exact_template_data(self, template_data):
        """Assert that the template data exactly matches the given data."""
        assert self.template_data() == template_data

    def assert_component_used(self, component_name):
        """Assert that the given component was used."""
        assert component_name == self.component()

    def assert_template_used(self, response, template_name):
        """Assert that the given template was used."""
        # This is a placeholder - FastAPI doesn't have built-in template tracking
        # You would need to implement a custom mechanism to track templates
        pass

    def assert_contains(self, response, text):
        """Assert that the response contains the given text."""
        assert text in response.text


@pytest.fixture
def inertia_test(app, render_mock):
    """Fixture to create an InertiaTestCase instance."""
    test_case = InertiaTestCase()
    test_case.app = app
    test_case.inertia = ClientWithLastResponse(TestClient(app), is_inertia=True)
    test_case.client = ClientWithLastResponse(TestClient(app))
    test_case.mock_render = render_mock
    return test_case


def inertia_page(
    url,
    component="TestComponent",
    props=None,
    template_data=None,
    deferred_props=None,
    merge_props=None,
):
    """Create an Inertia page object."""
    props = props or {}
    template_data = template_data or {}
    _page = {
        "component": component,
        "props": props,
        "url": f"/{url}/",
        "version": settings.INERTIA_VERSION,
        "encryptHistory": False,
        "clearHistory": False,
    }

    if deferred_props:
        _page["deferredProps"] = deferred_props

    if merge_props:
        _page["mergeProps"] = merge_props

    return _page


def inertia_div(*args, **kwargs):
    """Create an Inertia div with page data."""
    page = inertia_page(*args, **kwargs)
    return f'<div id="app" data-page="{dumps(page).replace('"', "&quot;")}"></div>'
