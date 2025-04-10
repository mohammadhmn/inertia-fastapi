import json
import warnings
from typing import Any, Dict

from .prop_classes import DeferredProp, MergeProp, OptionalProp


def model_to_dict(model: Any) -> Dict[str, Any]:
    """Convert a model to a dictionary, excluding password field."""
    # This is a simple implementation, might need customization based on your ORM
    if hasattr(model, "__dict__"):
        return {
            k: v
            for k, v in model.__dict__.items()
            if not k.startswith("_") and k != "password"
        }
    return {}


class InertiaJsonEncoder(json.JSONEncoder):
    """JSON encoder for Inertia responses"""

    def default(self, value: Any) -> Any:
        if hasattr(value.__class__, "InertiaMeta"):
            return {
                field: getattr(value, field)
                for field in value.__class__.InertiaMeta.fields
            }

        # Handle ORM models - adapt this to your ORM
        if hasattr(value, "__tablename__"):  # SQLAlchemy check
            return model_to_dict(value)

        # Handle query sets - adapt this to your ORM
        if hasattr(value, "__iter__") and hasattr(value, "all"):
            return [
                model_to_dict(obj) if hasattr(obj, "__tablename__") else obj
                for obj in value
            ]

        return super().default(value)


def lazy(prop: Any) -> OptionalProp:
    warnings.warn(
        "lazy is deprecated and will be removed in a future version. Please use optional instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return optional(prop)


def optional(prop: Any) -> OptionalProp:
    return OptionalProp(prop)


def defer(prop: Any, group: str = "default", merge: bool = False) -> DeferredProp:
    return DeferredProp(prop, group=group, merge=merge)


def merge(prop: Any) -> MergeProp:
    return MergeProp(prop)
