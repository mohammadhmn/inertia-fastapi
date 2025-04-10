# Inertia.js FastAPI Integration

This is a FastAPI integration for [Inertia.js](https://inertiajs.com/), allowing server-driven single-page applications using FastAPI.

## Features

-   Full Inertia.js protocol support
-   Server-side rendering (SSR) support
-   Lazy loaded props
-   Shared data across requests
-   Type hints for better IDE support

## Installation

```bash
pip install inertia-fastapi
```

## Quick Start

1. Set up your FastAPI app with Inertia:

```python
from fastapi import FastAPI, Request
from inertia import setup_inertia

app = FastAPI()

# Setup Inertia and get the inertia instance
inertia = setup_inertia(
    app=app,
    templates_dir="templates",
    shared_data_callback=lambda request: {"user": {"name": "Example"}}
)

# Create Inertia pages with inertia.method decorators
@inertia.get("/", "Home")
async def home(request: Request):
    return {
        "title": "Welcome",
        "message": "Hello from Inertia.js + FastAPI!"
    }
```

2. Create templates directory with base layout:

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>FastAPI Inertia</title>
        {% block inertia_head %}{% endblock %}
    </head>
    <body>
        {% block inertia %}{% endblock %}
        <script src="{{ url_for('static', path='js/app.js') }}"></script>
    </body>
</html>
```

3. Setup your Inertia.js frontend according to the [official documentation](https://inertiajs.com/).

## Usage

### Creating Inertia Routes

There are two ways to create Inertia routes:

#### 1. Using the Inertia Instance Decorators (Recommended)

The most concise way is to use the inertia instance's method decorators:

```python
# Setup returns an inertia instance
inertia = setup_inertia(app, "templates")

# Method-specific decorators
@inertia.get("/dashboard", "Dashboard")
async def dashboard(request: Request):
    return {
        "title": "Dashboard",
        "stats": get_stats()
    }

@inertia.post("/users", "UserCreate")
async def create_user(request: Request, name: str = Form(...)):
    # Create user
    return {
        "success": True
    }

# Multiple methods with the route decorator
@inertia.route(
    "/users/{user_id}",
    "UserEdit",
    methods=["GET", "PUT", "DELETE"]
)
async def user_edit(request: Request, user_id: int):
    # Handle different HTTP methods for the same component
    if request.method == "DELETE":
        # Delete user
        pass
    elif request.method == "PUT":
        # Update user
        pass

    # GET or after PUT/DELETE
    return {
        "user": get_user(user_id)
    }
```

#### 2. Using FastAPI Decorators with Inertia Decorator

You can also use FastAPI's route decorators combined with the inertia decorator:

```python
from inertia import inertia

@app.get("/dashboard")
@inertia("Dashboard")
async def dashboard(request: Request):
    return {
        "title": "Dashboard",
        "stats": get_stats()
    }
```

Both approaches achieve the same result, but the first one is more concise.

### Manual Rendering

If you need more control, you can directly use the render function:

```python
from inertia import render

@app.get("/contact")
async def contact(request: Request):
    """Contact page route"""
    return await render(
        request=request,
        component="Contact",
        props={"title": "Contact Us", "email": "contact@example.com"}
    )
```

### Sharing Data

You can share data across all Inertia responses for a request:

```python
from inertia import share

@app.get("/dashboard")
@inertia("Dashboard")
async def dashboard(request: Request):
    # Share user data with all Inertia responses
    share(request, user=current_user)
    return {"stats": get_stats()}
```

### Lazy Props

For expensive operations, you can defer loading:

```python
from inertia.utils import defer

@inertia.get("/dashboard", "Dashboard")
async def dashboard(request: Request):
    return {
        "stats": defer(lambda: get_expensive_stats(), group="stats"),
        "user": {"name": "John"}
    }
```

### Redirects

Inertia provides special handling for redirects:

```python
from fastapi.responses import RedirectResponse
from inertia import location

@app.post("/logout")
async def logout(request: Request):
    # Process logout...

    # Option 1: Use standard FastAPI redirect
    # (Inertia middleware will handle it)
    return RedirectResponse(url="/login")

    # Option 2: Use Inertia location helper
    return location("/login")
```

## Configuration

Configure Inertia in your application startup:

```python
inertia = setup_inertia(
    app=app,
    templates_dir="templates",  # Directory containing your Jinja2 templates
    shared_data_callback=lambda req: {"user": req.state.user}  # Optional callback for shared data
)
```

### Environment Variables

You can configure Inertia using environment variables:

-   `INERTIA_VERSION`: Asset version for cache busting (default: "1.0")
-   `INERTIA_SSR_URL`: SSR server URL (default: "http://localhost:13714")
-   `INERTIA_SSR_ENABLED`: Enable/disable SSR (default: False)
-   `INERTIA_ENCRYPT_HISTORY`: Encrypt history state (default: False)
-   `INERTIA_LAYOUT`: Base template to extend (default: "base.html")

## Server-Side Rendering

If you want to use server-side rendering:

1. Set the appropriate environment variables:

    ```python
    import os
    os.environ["INERTIA_SSR_ENABLED"] = "True"
    os.environ["INERTIA_SSR_URL"] = "http://localhost:13714"
    ```

2. Follow the [Inertia.js SSR setup documentation](https://inertiajs.com/server-side-rendering).

## License

MIT
