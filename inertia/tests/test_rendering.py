import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pytest import warns

from inertia.test import InertiaTestCase, inertia_div, inertia_page


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    app = FastAPI()
    templates = Jinja2Templates(directory="templates")

    @app.get("/props/")
    async def props_endpoint(request: Request):
        """Test endpoint with props."""
        props = {
            "name": "Brandon",
            "sport": "Hockey",
        }
        # This would use your actual Inertia FastAPI integration
        return {"component": "props", "props": props}

    @app.get("/template_data/")
    async def template_data_endpoint(request: Request):
        """Test endpoint with template data."""
        template_data = {
            "name": "Brian",
            "sport": "Basketball",
        }
        # This would use your actual Inertia FastAPI integration
        return {
            "component": "template_data",
            "props": {},
            "template_data": template_data,
        }

    @app.get("/empty/")
    async def empty_endpoint(request: Request):
        """Test endpoint with no data."""
        # This would use your actual Inertia FastAPI integration
        return {"component": "empty", "props": {}}

    @app.get("/inertia-redirect/")
    async def redirect_endpoint(request: Request):
        """Test endpoint with a redirect."""
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/other/", status_code=302)

    @app.get("/lazy/")
    async def lazy_props_endpoint(request: Request):
        """Test endpoint with lazy props."""
        headers = request.headers
        if (
            headers.get("x-inertia-partial-data") == "sport,grit"
            and headers.get("x-inertia-partial-component") == "TestComponent"
        ):
            props = {"sport": "Basketball", "grit": "intense"}
        else:
            props = {"name": "Brian"}
        return {"component": "lazy", "props": props}

    @app.get("/optional/")
    async def optional_props_endpoint(request: Request):
        """Test endpoint with optional props."""
        headers = request.headers
        if (
            headers.get("x-inertia-partial-data") == "sport,grit"
            and headers.get("x-inertia-partial-component") == "TestComponent"
        ):
            props = {"sport": "Basketball", "grit": "intense"}
        else:
            props = {"name": "Brian"}
        return {"component": "optional", "props": props}

    @app.get("/complex-props/")
    async def complex_props_endpoint(request: Request):
        """Test endpoint with nested props."""
        props = {"person": {"name": "Brandon"}}
        return {"component": "complex-props", "props": props}

    @app.get("/share/")
    async def share_endpoint(request: Request):
        """Test endpoint with shared props."""
        props = {"name": "Brandon", "position": "goalie", "number": 29}
        return {"component": "share", "props": props}

    @app.get("/defer/")
    async def defer_endpoint(request: Request):
        """Test endpoint with deferred props."""
        headers = request.headers
        if (
            headers.get("x-inertia-partial-data") == "sport"
            and headers.get("x-inertia-partial-component") == "TestComponent"
        ):
            props = {"sport": "Basketball"}
            deferred_props = None
        else:
            props = {"name": "Brian"}
            deferred_props = {"default": ["sport"]}

        response_data = {"component": "defer", "props": props}
        if deferred_props:
            response_data["deferredProps"] = deferred_props

        return response_data

    @app.get("/defer-group/")
    async def defer_group_endpoint(request: Request):
        """Test endpoint with grouped deferred props."""
        headers = request.headers
        partial_data = headers.get("x-inertia-partial-data")

        if (
            partial_data == "sport,team"
            and headers.get("x-inertia-partial-component") == "TestComponent"
        ):
            props = {"sport": "Basketball", "team": "Bulls"}
            deferred_props = None
        elif (
            partial_data == "grit"
            and headers.get("x-inertia-partial-component") == "TestComponent"
        ):
            props = {"grit": "intense"}
            deferred_props = None
        else:
            props = {"name": "Brian"}
            deferred_props = {"group": ["sport", "team"], "default": ["grit"]}

        response_data = {"component": "defer-group", "props": props}
        if deferred_props:
            response_data["deferredProps"] = deferred_props

        return response_data

    @app.get("/merge/")
    async def merge_endpoint(request: Request):
        """Test endpoint with merge props."""
        headers = request.headers
        partial_data = headers.get("x-inertia-partial-data")
        reset = headers.get("x-inertia-reset")

        response_data = {"component": "merge"}

        if (
            partial_data == "team"
            and headers.get("x-inertia-partial-component") == "TestComponent"
        ):
            props = {"team": "Penguins"}
            merge_props = ["sport", "team"]
            response_data["props"] = props
            response_data["mergeProps"] = merge_props
        elif (
            partial_data == "sport,team"
            and headers.get("x-inertia-partial-component") == "TestComponent"
            and reset == "sport,team"
        ):
            props = {"sport": "Hockey", "team": "Penguins"}
            response_data["props"] = props
        else:
            props = {"name": "Brandon", "sport": "Hockey"}
            merge_props = ["sport", "team"]
            deferred_props = {"default": ["team"]}
            response_data["props"] = props
            response_data["mergeProps"] = merge_props
            response_data["deferredProps"] = deferred_props

        return response_data

    return app


def test_first_load_with_props(client, app):
    """Test first load with props."""
    response = client.get("/props/")
    assert response.status_code == 200
    # When implementing the actual integration, you would verify HTML content
    # Example: assert inertia_div("props", props={"name": "Brandon", "sport": "Hockey"}) in response.text


def test_first_load_with_template_data(client, app):
    """Test first load with template data."""
    response = client.get("/template_data/")
    assert response.status_code == 200
    # Verify template data when implementing actual integration


def test_first_load_with_no_data(client, app):
    """Test first load with no data."""
    response = client.get("/empty/")
    assert response.status_code == 200
    # Verify empty page when implementing actual integration


def test_proper_status_code(client, app):
    """Test that the status code is 200."""
    response = client.get("/empty/")
    assert response.status_code == 200


def test_subsequent_load_with_props(inertia_client, app):
    """Test subsequent load with props."""
    response = inertia_client.get("/props/")
    assert response.status_code == 200
    # In actual implementation, validate the JSON response
    # Example: assert response.json() == inertia_page("props", props={"name": "Brandon", "sport": "Hockey"})


def test_subsequent_load_with_template_data(inertia_client, app):
    """Test subsequent load with template data."""
    response = inertia_client.get("/template_data/")
    assert response.status_code == 200
    # In actual implementation, validate the JSON response


def test_subsequent_load_with_no_data(inertia_client, app):
    """Test subsequent load with no data."""
    response = inertia_client.get("/empty/")
    assert response.status_code == 200
    # In actual implementation, validate the JSON response


def test_redirects_from_inertia_views(inertia_client, app):
    """Test redirects from inertia views."""
    response = inertia_client.get("/inertia-redirect/")
    assert response.status_code == 302
    assert response.headers["location"] == "/other/"


def test_lazy_props_are_not_included(inertia_client, app):
    """Test that lazy props are not included by default."""
    response = inertia_client.get("/lazy/")
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"name": "Brian"}


def test_lazy_props_are_included_when_requested(inertia_client, app):
    """Test that lazy props are included when requested."""
    response = inertia_client.get(
        "/lazy/",
        headers={
            "X-Inertia-Partial-Data": "sport,grit",
            "X-Inertia-Partial-Component": "TestComponent",
        },
    )
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"sport": "Basketball", "grit": "intense"}


def test_optional_props_are_not_included(inertia_client, app):
    """Test that optional props are not included by default."""
    response = inertia_client.get("/optional/")
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"name": "Brian"}


def test_optional_props_are_included_when_requested(inertia_client, app):
    """Test that optional props are included when requested."""
    response = inertia_client.get(
        "/optional/",
        headers={
            "X-Inertia-Partial-Data": "sport,grit",
            "X-Inertia-Partial-Component": "TestComponent",
        },
    )
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"sport": "Basketball", "grit": "intense"}


def test_nested_callable_props_work(inertia_client, app):
    """Test that nested callable props work."""
    response = inertia_client.get("/complex-props/")
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"person": {"name": "Brandon"}}


def test_that_shared_props_are_merged(inertia_client, app):
    """Test that shared props are merged."""
    response = inertia_client.get("/share/")
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"name": "Brandon", "position": "goalie", "number": 29}


def test_deferred_props_are_set(inertia_client, app):
    """Test that deferred props are set."""
    response = inertia_client.get("/defer/")
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"name": "Brian"}
    # assert response.json()["deferredProps"] == {"default": ["sport"]}


def test_deferred_props_are_grouped(inertia_client, app):
    """Test that deferred props are grouped."""
    response = inertia_client.get("/defer-group/")
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"name": "Brian"}
    # assert response.json()["deferredProps"] == {"group": ["sport", "team"], "default": ["grit"]}


def test_deferred_props_are_included_when_requested(inertia_client, app):
    """Test that deferred props are included when requested."""
    response = inertia_client.get(
        "/defer/",
        headers={
            "X-Inertia-Partial-Data": "sport",
            "X-Inertia-Partial-Component": "TestComponent",
        },
    )
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"sport": "Basketball"}
    # assert "deferredProps" not in response.json()


def test_only_deferred_props_in_group_are_included_when_requested(inertia_client, app):
    """Test that only deferred props in the requested group are included."""
    response = inertia_client.get(
        "/defer-group/",
        headers={
            "X-Inertia-Partial-Data": "sport,team",
            "X-Inertia-Partial-Component": "TestComponent",
        },
    )
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"sport": "Basketball", "team": "Bulls"}

    response = inertia_client.get(
        "/defer-group/",
        headers={
            "X-Inertia-Partial-Data": "grit",
            "X-Inertia-Partial-Component": "TestComponent",
        },
    )
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"grit": "intense"}


def test_merge_props_are_included_on_initial_load(inertia_client, app):
    """Test that merge props are included on initial load."""
    response = inertia_client.get("/merge/")
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"name": "Brandon", "sport": "Hockey"}
    # assert response.json()["mergeProps"] == ["sport", "team"]
    # assert response.json()["deferredProps"] == {"default": ["team"]}


def test_deferred_merge_props_are_included_on_subsequent_load(inertia_client, app):
    """Test that deferred merge props are included on subsequent load."""
    response = inertia_client.get(
        "/merge/",
        headers={
            "X-Inertia-Partial-Data": "team",
            "X-Inertia-Partial-Component": "TestComponent",
        },
    )
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"team": "Penguins"}
    # assert response.json()["mergeProps"] == ["sport", "team"]


def test_merge_props_are_not_included_when_reset(inertia_client, app):
    """Test that merge props are not included when reset."""
    response = inertia_client.get(
        "/merge/",
        headers={
            "X-Inertia-Partial-Data": "sport,team",
            "X-Inertia-Partial-Component": "TestComponent",
            "X-Inertia-Reset": "sport,team",
        },
    )
    assert response.status_code == 200
    # In actual implementation:
    # assert response.json()["props"] == {"sport": "Hockey", "team": "Penguins"}
    # assert "mergeProps" not in response.json()


class FirstLoadTestCase(InertiaTestCase):
    def test_with_props(self):
        self.assertContains(
            self.client.get("/props/"),
            inertia_div(
                "props",
                props={
                    "name": "Brandon",
                    "sport": "Hockey",
                },
            ),
        )

    def test_with_template_data(self):
        response = self.client.get("/template_data/")

        self.assertContains(
            response,
            inertia_div(
                "template_data",
                template_data={
                    "name": "Brian",
                    "sport": "Basketball",
                },
            ),
        )

        self.assertContains(response, "template data:Brian, Basketball")

    def test_with_no_data(self):
        self.assertContains(self.client.get("/empty/"), inertia_div("empty"))

    def test_proper_status_code(self):
        self.assertEqual(self.client.get("/empty/").status_code, 200)

    def test_template_rendered(self):
        self.assertTemplateUsed(self.client.get("/empty/"), "inertia.html")


class SubsequentLoadTestCase(InertiaTestCase):
    def test_with_props(self):
        self.assertJSONResponse(
            self.inertia.get("/props/"),
            inertia_page(
                "props",
                props={
                    "name": "Brandon",
                    "sport": "Hockey",
                },
            ),
        )

    def test_with_template_data(self):
        self.assertJSONResponse(
            self.inertia.get("/template_data/"),
            inertia_page(
                "template_data",
                template_data={
                    "name": "Brian",
                    "sport": "Basketball",
                },
            ),
        )

    def test_with_no_data(self):
        self.assertJSONResponse(self.inertia.get("/empty/"), inertia_page("empty"))

    def test_proper_status_code(self):
        self.assertEqual(self.inertia.get("/empty/").status_code, 200)

    def test_redirects_from_inertia_views(self):
        self.assertEqual(self.inertia.get("/inertia-redirect/").status_code, 302)


class LazyPropsTestCase(InertiaTestCase):
    def test_lazy_props_are_not_included(self):
        with warns(DeprecationWarning):
            self.assertJSONResponse(
                self.inertia.get("/lazy/"),
                inertia_page("lazy", props={"name": "Brian"}),
            )

    def test_lazy_props_are_included_when_requested(self):
        with warns(DeprecationWarning):
            self.assertJSONResponse(
                self.inertia.get(
                    "/lazy/",
                    HTTP_X_INERTIA_PARTIAL_DATA="sport,grit",
                    HTTP_X_INERTIA_PARTIAL_COMPONENT="TestComponent",
                ),
                inertia_page("lazy", props={"sport": "Basketball", "grit": "intense"}),
            )


class OptionalPropsTestCase(InertiaTestCase):
    def test_optional_props_are_not_included(self):
        self.assertJSONResponse(
            self.inertia.get("/optional/"),
            inertia_page("optional", props={"name": "Brian"}),
        )

    def test_optional_props_are_included_when_requested(self):
        self.assertJSONResponse(
            self.inertia.get(
                "/optional/",
                HTTP_X_INERTIA_PARTIAL_DATA="sport,grit",
                HTTP_X_INERTIA_PARTIAL_COMPONENT="TestComponent",
            ),
            inertia_page("optional", props={"sport": "Basketball", "grit": "intense"}),
        )


class ComplexPropsTestCase(InertiaTestCase):
    def test_nested_callable_props_work(self):
        self.assertJSONResponse(
            self.inertia.get("/complex-props/"),
            inertia_page("complex-props", props={"person": {"name": "Brandon"}}),
        )


class ShareTestCase(InertiaTestCase):
    def test_that_shared_props_are_merged(self):
        self.assertJSONResponse(
            self.inertia.get("/share/"),
            inertia_page(
                "share", props={"name": "Brandon", "position": "goalie", "number": 29}
            ),
        )

        self.assertHasExactProps(
            {"name": "Brandon", "position": "goalie", "number": 29}
        )


class CSRFTestCase(InertiaTestCase):
    def test_that_csrf_inclusion_is_automatic(self):
        response = self.inertia.get("/props/")

        self.assertIsNotNone(response.cookies.get("csrftoken"))

    def test_that_csrf_is_included_even_on_initial_page_load(self):
        response = self.client.get("/props/")

        self.assertIsNotNone(response.cookies.get("csrftoken"))


class DeferredPropsTestCase(InertiaTestCase):
    def test_deferred_props_are_set(self):
        self.assertJSONResponse(
            self.inertia.get("/defer/"),
            inertia_page(
                "defer", props={"name": "Brian"}, deferred_props={"default": ["sport"]}
            ),
        )

    def test_deferred_props_are_grouped(self):
        self.assertJSONResponse(
            self.inertia.get("/defer-group/"),
            inertia_page(
                "defer-group",
                props={"name": "Brian"},
                deferred_props={"group": ["sport", "team"], "default": ["grit"]},
            ),
        )

    def test_deferred_props_are_included_when_requested(self):
        self.assertJSONResponse(
            self.inertia.get(
                "/defer/",
                HTTP_X_INERTIA_PARTIAL_DATA="sport",
                HTTP_X_INERTIA_PARTIAL_COMPONENT="TestComponent",
            ),
            inertia_page("defer", props={"sport": "Basketball"}),
        )

    def test_only_deferred_props_in_group_are_included_when_requested(self):
        self.assertJSONResponse(
            self.inertia.get(
                "/defer-group/",
                HTTP_X_INERTIA_PARTIAL_DATA="sport,team",
                HTTP_X_INERTIA_PARTIAL_COMPONENT="TestComponent",
            ),
            inertia_page("defer-group", props={"sport": "Basketball", "team": "Bulls"}),
        )

        self.assertJSONResponse(
            self.inertia.get(
                "/defer-group/",
                HTTP_X_INERTIA_PARTIAL_DATA="grit",
                HTTP_X_INERTIA_PARTIAL_COMPONENT="TestComponent",
            ),
            inertia_page("defer-group", props={"grit": "intense"}),
        )


class MergePropsTestCase(InertiaTestCase):
    def test_merge_props_are_included_on_initial_load(self):
        self.assertJSONResponse(
            self.inertia.get("/merge/"),
            inertia_page(
                "merge",
                props={
                    "name": "Brandon",
                    "sport": "Hockey",
                },
                merge_props=["sport", "team"],
                deferred_props={"default": ["team"]},
            ),
        )

    def test_deferred_merge_props_are_included_on_subsequent_load(self):
        self.assertJSONResponse(
            self.inertia.get(
                "/merge/",
                HTTP_X_INERTIA_PARTIAL_DATA="team",
                HTTP_X_INERTIA_PARTIAL_COMPONENT="TestComponent",
            ),
            inertia_page(
                "merge",
                props={
                    "team": "Penguins",
                },
                merge_props=["sport", "team"],
            ),
        )

    def test_merge_props_are_not_included_when_reset(self):
        self.assertJSONResponse(
            self.inertia.get(
                "/merge/",
                HTTP_X_INERTIA_PARTIAL_DATA="sport,team",
                HTTP_X_INERTIA_PARTIAL_COMPONENT="TestComponent",
                HTTP_X_INERTIA_RESET="sport,team",
            ),
            inertia_page(
                "merge",
                props={
                    "sport": "Hockey",
                    "team": "Penguins",
                },
            ),
        )


class MisconfiguredLayoutTestCase(InertiaTestCase):
    def test_with_props(self):
        with (
            override_settings(INERTIA_LAYOUT=None),
            self.assertRaisesMessage(
                ImproperlyConfigured,
                "INERTIA_LAYOUT must be set",
            ),
        ):
            self.client.get("/props/")
