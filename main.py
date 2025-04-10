from http import HTTPStatus
from typing import Any, Dict, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from inertia.http import render, setup_inertia

# Create FastAPI application
app = FastAPI(title="FastAPI Inertia.js Example")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Initialize Inertia.js
def shared_data(request: Request) -> Dict[str, Any]:
    """Provide shared data for all Inertia requests"""
    return {
        "user": {"name": "Example User"},  # Example shared data
        "app_name": "FastAPI Inertia Example",
    }


# Set up Inertia with FastAPI and get the inertia instance
inertia = setup_inertia(
    app=app, templates_dir="templates", shared_data_callback=shared_data
)


# Define routes using the new style decorators
@inertia.get("/", "Home")
async def home(request: Request):
    """Home page route"""
    return {
        "title": "Welcome to FastAPI Inertia",
        "message": "This is an example Inertia.js page with FastAPI",
    }


@inertia.get("/about", "About")
async def about(request: Request):
    """About page route"""
    return {"title": "About", "content": "This is the about page content"}


# Example with form handling using multiple HTTP methods
@inertia.route("/form", "Form", methods=["GET", "POST"])
async def form_example(
    request: Request,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
):
    """Form handling example"""
    success_message = None

    # Check if this is a POST request with form data
    if request.method == "POST" and name and email:
        # Process the form data
        success_message = f"Form submitted successfully for {name} ({email})"

    # Return props for the component
    return {
        "title": "Form Example",
        "success_message": success_message,
        "form_data": {"name": name or "", "email": email or ""},
    }


# Example of a redirect that will be handled by the Inertia middleware
@app.get("/redirect-example")
async def redirect_example():
    """Redirect example that will be handled by the Inertia middleware"""
    return RedirectResponse(url="/about", status_code=HTTPStatus.FOUND)


# Example of a PUT endpoint that redirects (will be converted to 303 by middleware)
@app.put("/put-redirect")
async def put_redirect():
    """PUT endpoint that redirects - will be converted to 303 by middleware"""
    return RedirectResponse(url="/about", status_code=HTTPStatus.FOUND)


# Direct rendering example without decorator
@app.get("/contact")
async def contact(request: Request):
    """Contact page route"""
    return await render(
        request=request,
        component="Contact",
        props={"title": "Contact Us", "email": "contact@example.com"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
